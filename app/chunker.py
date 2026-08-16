from __future__ import annotations

import hashlib

from .models import ChunkDocument, PageDocument

SEPARATORS = ["\n\n", "\n", ". ", "; ", ", ", " ", ""]


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


def chunk_page(
    page: PageDocument,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> list[ChunkDocument]:
    if not 800 <= chunk_size <= 1200:
        raise ValueError("chunk_size must be between 800 and 1200 characters.")
    if not 100 <= overlap <= 200:
        raise ValueError("overlap must be between 100 and 200 characters.")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    # Base segments leave room for overlap so final chunks never exceed chunk_size.
    base_segments = _recursive_segments(page.text, chunk_size - overlap, SEPARATORS)
    chunks: list[ChunkDocument] = []
    previous = ""

    for index, segment in enumerate(base_segments):
        prefix = previous[-overlap:] if previous else ""
        text = (prefix + ("\n" if prefix else "") + segment).strip()
        if len(text) > chunk_size:
            text = text[-chunk_size:]

        embedded_text = (
            f"Source: {page.source}\n"
            f"Quarter: {page.quarter}\n"
            f"Page: {page.page}\n\n"
            f"{text}"
        )
        chunks.append(
            ChunkDocument(
                id=_stable_chunk_id(page.source, page.page, index),
                text=text,
                embedded_text=embedded_text,
                source=page.source,
                page=page.page,
                quarter=page.quarter,
                chunk_index=index,
            )
        )
        previous = segment

    return chunks


def chunk_pages(
    pages: list[PageDocument],
    chunk_size: int = 1200,
    overlap: int = 150,
) -> list[ChunkDocument]:
    chunks: list[ChunkDocument] = []
    for page in pages:
        chunks.extend(chunk_page(page, chunk_size=chunk_size, overlap=overlap))
    return chunks
