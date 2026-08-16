from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PageDocument:
    text: str
    source: str
    page: int
    quarter: str


@dataclass(frozen=True)
class ChunkDocument:
    id: str
    text: str
    embedded_text: str
    source: str
    page: int
    quarter: str
    chunk_index: int


@dataclass(frozen=True)
class RetrievedChunk:
    text: str
    source: str
    page: int
    quarter: str
    distance: float | None = None

    @property
    def similarity(self) -> float | None:
        # Chroma is configured for cosine distance: distance = 1 - cosine_similarity.
        if self.distance is None:
            return None
        return 1.0 - self.distance
