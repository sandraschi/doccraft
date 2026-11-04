"""Unit and integration tests for DocCraft CLI verbs."""

import json
from pathlib import Path

import pytest
from doccraft import cli
from pypdf import PageObject, PdfReader, PdfWriter


def _create_sample_pdf(path: Path, text: str = "DocCraft Test Page") -> Path:
    writer = PdfWriter()
    # Create empty blank page (letter size)
    page = PageObject.create_blank_page(width=612, height=792)
    writer.add_page(page)
    with path.open("wb") as f:
        writer.write(f)
    return path


def test_info(tmp_path):
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("Hello DocCraft!", encoding="utf-8")

    info = cli.get_info(txt_file)
    assert info["filename"] == "sample.txt"
    assert info["family"] == "text"
    assert info["size_bytes"] > 0


def test_text_extraction_md(tmp_path):
    md_file = tmp_path / "doc.md"
    content = "# Document Title\n\nThis is paragraph one with important details."
    md_file.write_text(content, encoding="utf-8")

    res = cli.extract_text(md_file)
    assert res["format"] == "md"
    assert res["word_count"] > 5
    assert "Document Title" in res["text"]


def test_combine_pdfs(tmp_path):
    pdf1 = _create_sample_pdf(tmp_path / "page1.pdf")
    pdf2 = _create_sample_pdf(tmp_path / "page2.pdf")
    merged = tmp_path / "merged.pdf"

    res = cli.combine_pdfs([pdf1, pdf2], merged)
    assert res["success"] is True
    assert res["total_pages"] == 2
    assert merged.is_file()

    reader = PdfReader(str(merged))
    assert len(reader.pages) == 2


def test_convert_document(tmp_path):
    md_file = tmp_path / "source.md"
    md_file.write_text("# Test Document\n\nAutomated testing.", encoding="utf-8")

    # If LibreOffice is present, test HTML conversion
    res = cli.convert_document(md_file, "html", out_dir=tmp_path / "out")
    assert res["success"] is True
    out_file = Path(res["output"])
    assert out_file.is_file()


def test_cli_runner(tmp_path, capsys):
    pdf1 = _create_sample_pdf(tmp_path / "a.pdf")
    pdf2 = _create_sample_pdf(tmp_path / "b.pdf")
    merged = tmp_path / "out.pdf"

    # Test combine CLI
    rc = cli.main(["combine", str(pdf1), str(pdf2), "--out", str(merged), "--json"])
    assert rc == 0
    captured = capsys.readouterr()
    comb_json = json.loads(captured.out)
    assert comb_json["total_pages"] == 2

    # Test info CLI
    rc = cli.main(["info", "--in", str(merged), "--json"])
    assert rc == 0
    captured = capsys.readouterr()
    info_json = json.loads(captured.out)
    assert info_json["page_count"] == 2
