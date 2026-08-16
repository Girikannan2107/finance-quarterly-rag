from __future__ import annotations

import hashlib
import re

from .models import ChunkDocument, PageDocument

SEPARATORS = ["\n\n", "\n", ". ", "; ", ", ", " ", ""]

# Patterns to detect financial table elements
FINANCIAL_TABLE_INDICATORS = [
    r"(?:Quarter|Q[1-4])\s*(?:ended|FY|FY\d{2})",  # Quarter headers
    r"(?:Revenue|Income|Profit|Loss|Earnings|EBITDA|Margin)",  # Financial terms
    r"(?:₹|Rupees|Rs\.|Crores|Million|INR)",  # Currency
    r"(?:\d{1,3}(?:,\d{3})*|\d+)",  # Numbers with/without formatting
    r"(?:Year-on-year|YoY|Consolidated|Standalone)",  # Financial contexts
]


def _recursive_segments(text: str, max_size: int, separators: list[str]) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_size:
        return [text]

    separator = separators[0]
    remaining = separators[1:]
    if separator == "":
        return [text[i : i + max_size] for i in range(0, len(text), max_size)]

    parts = text.split(separator)
    segments: list[str] = []
    current = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue
        candidate = part if not current else current + separator + part
        if len(candidate) <= max_size:
            current = candidate
            continue

        if current:
            segments.append(current)
            current = ""

        if len(part) <= max_size:
            current = part
        else:
            segments.extend(_recursive_segments(part, max_size, remaining or [""]))

    if current:
        segments.append(current)
    return segments


def _stable_chunk_id(source: str, page: int, chunk_index: int) -> str:
    raw = f"{source}|{page}|{chunk_index}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def _is_financial_table_line(line: str) -> bool:
    """Check if a line appears to be part of a financial table."""
    if len(line.strip()) < 10:
        return False
    
    # Check for currency and numbers
    has_currency = bool(re.search(r"[₹$€£]|\b(?:crores|million|thousand|lakh)\b", line, re.I))
    has_numbers = bool(re.search(r"\d+(?:[,\.]\d{3})*(?:\.\d+)?", line))
    has_financial_term = any(re.search(pattern, line, re.I) for pattern in FINANCIAL_TABLE_INDICATORS)
    
    return (has_currency and has_numbers) or (has_financial_term and has_numbers)


def _detect_financial_content_level(text: str) -> int:
    """
    Detect how heavily financial-table-focused this text is.
    Returns 0-2: 0=none, 1=some, 2=high (likely a table or financial statement).
    """
    if not text:
        return 0
    
    lines = text.split("\n")
    financial_lines = sum(1 for line in lines if _is_financial_table_line(line))
    
    if not lines:
        return 0
    
    ratio = financial_lines / len(lines)
    
    if ratio >= 0.5:
        return 2  # High concentration of financial data
    elif ratio >= 0.2:
        return 1  # Some financial data
    else:
        return 0  # Low or no financial data


def _chunk_page_financial_aware(
    page: PageDocument,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> list[ChunkDocument]:
    """
    Improved chunking that preserves financial table structure better.
    For high-financial-content sections, uses more conservative splitting.
    """
    if not 800 <= chunk_size <= 1200:
        raise ValueError("chunk_size must be between 800 and 1200 characters.")
    if not 100 <= overlap <= 200:
        raise ValueError("overlap must be between 100 and 200 characters.")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")
    
    text = page.text
    chunks: list[ChunkDocument] = []
    chunk_index = 0
    
    # Split by double newline first (usually paragraphs/sections)
    sections = text.split("\n\n")
    
    position = 0  # Track position in full text for overlap calculation
    
    for section in sections:
        if not section.strip():
            continue
        
        # Check if this section is financial data
        financial_level = _detect_financial_content_level(section)
        
        # For high-financial-content sections, try to keep them together
        if financial_level == 2 and len(section) <= chunk_size:
            # Entire section fits in one chunk - keep it together
            prefix = text[max(0, position - overlap):position][-overlap:] if position > 0 else ""
            full_text = (prefix + ("\n" if prefix else "") + section).strip()
            
            if len(full_text) > chunk_size:
                # Still too large, trim from end
                full_text = full_text[-chunk_size:]
            
            embedded_text = (
                f"Source: {page.source}\n"
                f"Quarter: {page.quarter}\n"
                f"Page: {page.page}\n\n"
                f"{full_text}"
            )
            
            chunks.append(
                ChunkDocument(
                    id=_stable_chunk_id(page.source, page.page, chunk_index),
                    text=full_text,
                    embedded_text=embedded_text,
                    source=page.source,
                    page=page.page,
                    quarter=page.quarter,
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1
            position += len(section) + 2  # +2 for the \n\n
            continue
        
        # For normal sections or large financial sections, use regular chunking
        base_segments = _recursive_segments(section, chunk_size - overlap, SEPARATORS)
        previous = ""
        
        for segment in base_segments:
            if not segment.strip():
                continue
            
            prefix = previous[-overlap:] if previous else ""
            chunk_text = (prefix + ("\n" if prefix else "") + segment).strip()
            
            if len(chunk_text) > chunk_size:
                chunk_text = chunk_text[-chunk_size:]
            
            embedded_text = (
                f"Source: {page.source}\n"
                f"Quarter: {page.quarter}\n"
                f"Page: {page.page}\n\n"
                f"{chunk_text}"
            )
            
            chunks.append(
                ChunkDocument(
                    id=_stable_chunk_id(page.source, page.page, chunk_index),
                    text=chunk_text,
                    embedded_text=embedded_text,
                    source=page.source,
                    page=page.page,
                    quarter=page.quarter,
                    chunk_index=chunk_index,
                )
            )
            chunk_index += 1
            previous = segment
    
    return chunks


def chunk_page(
    page: PageDocument,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> list[ChunkDocument]:
    """Use financial-aware chunking strategy."""
    return _chunk_page_financial_aware(page, chunk_size=chunk_size, overlap=overlap)


def chunk_pages(
    pages: list[PageDocument],
    chunk_size: int = 1200,
    overlap: int = 150,
) -> list[ChunkDocument]:
    chunks: list[ChunkDocument] = []
    for page in pages:
        chunks.extend(chunk_page(page, chunk_size=chunk_size, overlap=overlap))
    return chunks
