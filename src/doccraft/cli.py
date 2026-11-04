"""DocCraft CLI: Headless verbs for office document conversion and manipulation."""

from __future__ import annotations

import argparse
import html
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from pypdf import PdfReader, PdfWriter


def find_soffice() -> Path | None:
    """Locate LibreOffice soffice executable across standard locations."""
    env_path = os.environ.get("LIBREOFFICE_SOFFICE_PATH") or os.environ.get("SOFFICE_PATH")
    if env_path and Path(env_path).is_file():
        return Path(env_path)

    which = shutil.which("soffice") or shutil.which("soffice.exe")
    if which and Path(which).is_file():
        return Path(which)

    candidates = (
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
    )
    for cand in candidates:
        if cand.is_file():
            return cand

    return None


def detect_family(file_path: Path) -> str:
    ext = file_path.suffix.lower()
    if ext in {".pdf"}:
        return "pdf"
    if ext in {".docx", ".doc", ".odt", ".rtf", ".txt", ".md", ".html"}:
        return "text"
    if ext in {".xlsx", ".xls", ".ods", ".csv"}:
        return "spreadsheet"
    if ext in {".pptx", ".ppt", ".odp"}:
        return "presentation"
    return "unknown"


def convert_document(
    input_path: Path,
    output_format: str,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    """Convert office document to target format (pdf, docx, odt, txt, html, etc.)."""
    if not input_path.is_file():
        raise FileNotFoundError(f"File not found: {input_path}")

    target_dir = out_dir or input_path.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    out_format = output_format.lstrip(".").lower()

    # Markdown to HTML/PDF helper
    src_file = input_path
    temp_html: Path | None = None
    if input_path.suffix.lower() in {".md", ".markdown"}:
        raw_md = input_path.read_text(encoding="utf-8")
        escaped_body = html.escape(raw_md).replace("\n", "<br/>\n")
        html_content = (
            f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>{input_path.stem}</title></head>"
            f"<body><pre>{escaped_body}</pre></body></html>"
        )
        if out_format in {"html", "htm"}:
            dest = target_dir / f"{input_path.stem}.html"
            dest.write_text(html_content, encoding="utf-8")
            return {
                "success": True,
                "input": str(input_path),
                "output": str(dest),
                "output_bytes": dest.stat().st_size,
                "engine": "internal_markdown",
                "format": "html",
            }

        import tempfile

        temp_html = Path(tempfile.gettempdir()) / f"doccraft_{os.getpid()}_{input_path.stem}.html"
        temp_html.write_text(html_content, encoding="utf-8")
        src_file = temp_html

    soffice = find_soffice()
    if not soffice:
        # Fallback if soffice absent: simple text or html export
        if out_format in {"txt", "html", "md"}:
            dest = target_dir / f"{input_path.stem}.{out_format}"
            dest.write_text(input_path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
            return {
                "success": True,
                "input": str(input_path),
                "output": str(dest),
                "engine": "fallback",
                "format": out_format,
            }
        return {
            "success": False,
            "error": "LibreOffice soffice executable not found in PATH or standard install dirs",
            "soffice_found": False,
        }

    cmd = [
        str(soffice),
        "--headless",
        "--norestore",
        "--invisible",
        "--convert-to",
        out_format,
        "--outdir",
        str(target_dir.resolve()),
        str(src_file.resolve()),
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        temp_out = target_dir / f"{src_file.stem}.{out_format}"
        expected_out = target_dir / f"{input_path.stem}.{out_format}"
        if temp_out.is_file() and temp_out != expected_out:
            if expected_out.is_file():
                expected_out.unlink()
            temp_out.rename(expected_out)

        return {
            "success": expected_out.is_file(),
            "input": str(input_path),
            "output": str(expected_out) if expected_out.is_file() else None,
            "output_bytes": expected_out.stat().st_size if expected_out.is_file() else 0,
            "engine": "libreoffice",
            "format": out_format,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    finally:
        if temp_html and temp_html.is_file():
            try:
                temp_html.unlink()
            except Exception:
                pass


def extract_text(input_path: Path) -> dict[str, Any]:
    """Extract text from document (PDF, TXT, MD, or office formats)."""
    if not input_path.is_file():
        raise FileNotFoundError(f"File not found: {input_path}")

    ext = input_path.suffix.lower()

    if ext == ".pdf":
        reader = PdfReader(str(input_path))
        pages_text: list[str] = []
        for p in reader.pages:
            t = p.extract_text() or ""
            pages_text.append(t)
        full_text = "\n\n".join(pages_text)
        return {
            "file": str(input_path),
            "format": "pdf",
            "page_count": len(reader.pages),
            "char_count": len(full_text),
            "word_count": len(full_text.split()),
            "text": full_text,
        }

    if ext in {".txt", ".md", ".html", ".csv", ".json", ".xml"}:
        text = input_path.read_text(encoding="utf-8", errors="replace")
        return {
            "file": str(input_path),
            "format": ext.lstrip("."),
            "char_count": len(text),
            "word_count": len(text.split()),
            "text": text,
        }

    # Use soffice to convert to txt
    soffice = find_soffice()
    if soffice:
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            res = convert_document(input_path, "txt:Text", out_dir=Path(tmpdir))
            if res.get("success") and res.get("output"):
                txt = Path(res["output"]).read_text(encoding="utf-8", errors="replace")
                return {
                    "file": str(input_path),
                    "format": ext.lstrip("."),
                    "char_count": len(txt),
                    "word_count": len(txt.split()),
                    "text": txt,
                }

    return {
        "file": str(input_path),
        "format": ext.lstrip("."),
        "error": "Direct text extraction not available without LibreOffice conversion",
    }


def get_info(input_path: Path) -> dict[str, Any]:
    """Inspect document metadata, file family, size, and page metrics."""
    if not input_path.is_file():
        raise FileNotFoundError(f"File not found: {input_path}")

    stat = input_path.stat()
    family = detect_family(input_path)
    info: dict[str, Any] = {
        "file": str(input_path),
        "filename": input_path.name,
        "extension": input_path.suffix.lower(),
        "family": family,
        "size_bytes": stat.st_size,
        "modified": stat.st_mtime,
    }

    if input_path.suffix.lower() == ".pdf":
        try:
            reader = PdfReader(str(input_path))
            info["page_count"] = len(reader.pages)
            meta = reader.metadata
            if meta:
                info["pdf_metadata"] = {
                    "title": meta.title,
                    "author": meta.author,
                    "creator": meta.creator,
                    "producer": meta.producer,
                }
        except Exception as e:
            info["pdf_error"] = str(e)

    soffice = find_soffice()
    info["soffice_available"] = bool(soffice)
    if soffice:
        info["soffice_path"] = str(soffice)

    return info


def combine_pdfs(input_paths: list[Path], out_file: Path) -> dict[str, Any]:
    """Merge multiple PDF documents into a combined output PDF."""
    if not input_paths:
        raise ValueError("At least one input file required")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    writer = PdfWriter()
    total_pages = 0

    for p in input_paths:
        if not p.is_file():
            raise FileNotFoundError(f"Input file not found: {p}")
        reader = PdfReader(str(p))
        total_pages += len(reader.pages)
        for page in reader.pages:
            writer.add_page(page)

    with out_file.open("wb") as f:
        writer.write(f)

    return {
        "success": True,
        "inputs": [str(p) for p in input_paths],
        "output": str(out_file),
        "total_pages": total_pages,
        "size_bytes": out_file.stat().st_size,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="doccraft",
        description="DocCraft: Office document conversion and manipulation CLI",
    )
    parser.add_argument("--version", action="version", version="doccraft 0.1.0")

    sub = parser.add_subparsers(dest="verb", required=True)

    # convert
    p_conv = sub.add_parser("convert", help="Convert office document format")
    p_conv.add_argument("--in", dest="input_file", required=True, type=Path, help="Input document")
    p_conv.add_argument("--out", dest="output_format", required=True, help="Target format or file path")
    p_conv.add_argument("--outdir", dest="out_dir", type=Path, help="Output directory")
    p_conv.add_argument("--json", action="store_true", help="Output JSON")

    # text
    p_txt = sub.add_parser("text", help="Extract text from document")
    p_txt.add_argument("--in", dest="input_file", required=True, type=Path, help="Input document")
    p_txt.add_argument("--json", action="store_true", help="Output JSON")

    # info
    p_info = sub.add_parser("info", help="Inspect document metadata")
    p_info.add_argument("--in", dest="input_file", required=True, type=Path, help="Input document")
    p_info.add_argument("--json", action="store_true", help="Output JSON")

    # combine
    p_comb = sub.add_parser("combine", help="Combine multiple documents (PDF)")
    p_comb.add_argument("inputs", nargs="+", type=Path, help="Input PDF files")
    p_comb.add_argument("--out", dest="out_file", required=True, type=Path, help="Output combined PDF")
    p_comb.add_argument("--json", action="store_true", help="Output JSON")

    # mcp
    sub.add_parser("mcp", help="Run FastMCP stdio server")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.verb == "convert":
            res = convert_document(args.input_file, args.output_format, out_dir=args.out_dir)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                if res.get("success"):
                    print(f"Converted: {res['input']} -> {res['output']} ({res.get('output_bytes', 0)} bytes)")
                else:
                    print(f"Conversion failed: {res.get('error')}", file=sys.stderr)
                    return 1
            return 0

        if args.verb == "text":
            res = extract_text(args.input_file)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"File: {res.get('file')} ({res.get('format')})")
                print(f"Words: {res.get('word_count', 0)} | Characters: {res.get('char_count', 0)}")
                print("--- Text ---")
                print(res.get("text", "")[:500])
            return 0

        if args.verb == "info":
            res = get_info(args.input_file)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"File: {res['filename']} ({res['family']}, {res['size_bytes']} bytes)")
                if "page_count" in res:
                    print(f"Pages: {res['page_count']}")
                if "soffice_available" in res:
                    print(f"LibreOffice backend available: {res['soffice_available']}")
            return 0

        if args.verb == "combine":
            res = combine_pdfs(args.inputs, args.out_file)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"Combined {len(res['inputs'])} files -> {res['output']} ({res['total_pages']} pages)")
            return 0

        if args.verb == "mcp":
            from .mcp_server import mcp

            mcp.run()
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
