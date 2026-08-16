from app.chunker import chunk_page
from app.models import PageDocument


def test_chunks_respect_limits_and_metadata():
    text = ("Revenue from operations was ₹30,246 crore. " * 100).strip()
    page = PageDocument(text=text, source="HCLTech_Q4_FY25.pdf", page=2, quarter="Q4 FY25")
    chunks = chunk_page(page, chunk_size=1200, overlap=150)
    assert chunks
    assert all(len(c.text) <= 1200 for c in chunks)
    assert all(c.source == page.source and c.page == 2 and c.quarter == "Q4 FY25" for c in chunks)
    assert all("Quarter: Q4 FY25" in c.embedded_text for c in chunks)


def test_stable_ids_prevent_duplicate_identity():
    page = PageDocument(text="A" * 3000, source="same.pdf", page=1, quarter="Q1 FY25")
    first = chunk_page(page)
    second = chunk_page(page)
    assert [c.id for c in first] == [c.id for c in second]
