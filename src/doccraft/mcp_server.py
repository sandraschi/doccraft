"""FastMCP server for DocCraft."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from .cli import combine_pdfs, convert_document, extract_text, find_soffice, get_info

mcp = FastMCP("DocCraft", version="0.1.0")


@mcp.tool()
def convert(input_path: str, output_format: str, output_dir: str | None = None) -> dict[str, Any]:
    """Convert an office document to target format (pdf, docx, odt, html, txt, xlsx, pptx)."""
    out = Path(output_dir) if output_dir else None
    return convert_document(Path(input_path), output_format, out_dir=out)


@mcp.tool()
def text(input_path: str) -> dict[str, Any]:
    """Extract full readable text and word counts from a document (PDF, Office, Markdown)."""
    return extract_text(Path(input_path))


@mcp.tool()
def info(input_path: str) -> dict[str, Any]:
    """Inspect document metadata, format family, size, and page counts."""
    return get_info(Path(input_path))


@mcp.tool()
def combine(input_paths: list[str], output_path: str) -> dict[str, Any]:
    """Merge multiple PDF documents into a combined output PDF."""
    sources = [Path(p) for p in input_paths]
    return combine_pdfs(sources, Path(output_path))


@mcp.tool()
def status() -> dict[str, Any]:
    """Inspect DocCraft runtime status and LibreOffice binary detection."""
    soffice = find_soffice()
    return {
        "status": "ready" if soffice else "degraded",
        "soffice_available": bool(soffice),
        "soffice_path": str(soffice) if soffice else None,
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
