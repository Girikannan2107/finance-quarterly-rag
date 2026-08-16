from __future__ import annotations

import io
import re
from pathlib import Path
from typing import BinaryIO

from pypdf import PdfReader

from .models import PageDocument


class PDFExtractionError(RuntimeError):
    pass


class ScannedPDFError(PDFExtractionError):
    pass


def _fy_label(end_year: int, quarter: int) -> str:
    # Indian April-March financial year: Jun/Sep/Dec 2024 => FY25; Mar 2025 => FY25.
    fy_end_year = end_year + 1 if quarter in (1, 2, 3) else end_year
    return f"Q{quarter} FY{str(fy_end_year)[-2:]}"


def infer_quarter(filename: str, text: str) -> str:
    normalized_name = filename.upper().replace("-", "_").replace(" ", "_")
    match = re.search(r"Q([1-4])_?FY_?(\d{2,4})", normalized_name)
    if match:
        q = int(match.group(1))
        fy = match.group(2)
        fy = fy[-2:]
        return f"Q{q} FY{fy}"

    compact = " ".join(text.split())
    patterns = [
        (1, r"quarter(?:\s+and[^.]{0,60})?\s+ended\s+(?:on\s+)?(?:30\s+June|June\s+30)[,\s]+(20\d{2})"),
        (2, r"quarter(?:\s+and[^.]{0,60})?\s+ended\s+(?:on\s+)?(?:30\s+September|September\s+30)[,\s]+(20\d{2})"),
        (3, r"quarter(?:\s+and[^.]{0,60})?\s+ended\s+(?:on\s+)?(?:31\s+December|December\s+31)[,\s]+(20\d{2})"),
        (4, r"quarter(?:\s+and[^.]{0,60})?\s+year\s+ended\s+(?:on\s+)?(?:31\s+March|March\s+31)[,\s]+(20\d{2})"),
        (4, r"quarter\s+ended\s+(?:on\s+)?(?:31\s+March|March\s+31)[,\s]+(20\d{2})"),
    ]
    for quarter, pattern in patterns:
        found = re.search(pattern, compact, flags=re.IGNORECASE)
        if found:
            return _fy_label(int(found.group(1)), quarter)

    # More permissive fallback for official result PDFs whose title formatting varies.
    date_patterns = [
        (1, r"(?:30\s+June|June\s+30)[,\s]+(20\d{2})"),
        (2, r"(?:30\s+September|September\s+30)[,\s]+(20\d{2})"),
        (3, r"(?:31\s+December|December\s+31)[,\s]+(20\d{2})"),
        (4, r"(?:31\s+March|March\s+31)[,\s]+(20\d{2})"),
    ]
    for quarter, pattern in date_patterns:
        found = re.search(pattern, compact, flags=re.IGNORECASE)
        if found:
            return _fy_label(int(found.group(1)), quarter)

    raise PDFExtractionError(
        f"Could not infer quarter for {filename}. Rename it like Company_Q1_FY25.pdf."
    )


def _read_pdf(reader: PdfReader, source_name: str) -> list[PageDocument]:
    if not reader.pages:
        raise PDFExtractionError(f"{source_name} contains no pages.")

    raw_pages: list[tuple[int, str]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:
            raise PDFExtractionError(
                f"Failed extracting page {page_number} from {source_name}: {exc}"
            ) from exc
        raw_pages.append((page_number, text.strip()))

    if not any(text for _, text in raw_pages):
        raise ScannedPDFError(
            f"{source_name} produced no selectable text and appears scanned/image-based."
        )

    sample = "\n".join(text for _, text in raw_pages[:3] if text)
    quarter = infer_quarter(source_name, sample)

    return [
        PageDocument(text=text, source=source_name, page=page_number, quarter=quarter)
        for page_number, text in raw_pages
        if text
    ]


def extract_pdf(path: str | Path, source_name: str | None = None) -> list[PageDocument]:
    path = Path(path)
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise PDFExtractionError(f"Unable to open {path.name}: {exc}") from exc
    return _read_pdf(reader, source_name or path.name)


def extract_pdf_bytes(data: bytes | BinaryIO, filename: str) -> list[PageDocument]:
    stream = io.BytesIO(data) if isinstance(data, bytes) else data
    try:
        reader = PdfReader(stream)
    except Exception as exc:
        raise PDFExtractionError(f"Unable to open {filename}: {exc}") from exc
    return _read_pdf(reader, filename)
