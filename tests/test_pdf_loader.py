from pathlib import Path

from app.pdf_loader import extract_pdf


def test_hcltech_q1_extracts_text():
    path = Path(__file__).resolve().parent.parent / "data" / "pdfs" / "HCLTech_Q1_FY25.pdf"
    pages = extract_pdf(path)
    assert pages
    assert pages[0].quarter == "Q1 FY25"
    assert pages[0].source == "HCLTech_Q1_FY25.pdf"
    assert pages[0].page == 1
    assert any("HCL" in page.text for page in pages[:3])
