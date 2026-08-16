from __future__ import annotations

from pathlib import Path

from .config import CHROMA_DIR, COLLECTION_NAME
from .models import ChunkDocument, RetrievedChunk


class ChromaStore:
    def __init__(
        self,
        persist_dir: str | Path = CHROMA_DIR,
        collection_name: str = COLLECTION_NAME,
    ):
        try:
            import chromadb
        except ImportError as exc:
            raise RuntimeError(
                "chromadb is not installed. Run: pip install -r requirements.txt"
            ) from exc

        persist_dir = Path(persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            configuration={"hnsw": {"space": "cosine"}},
        )

    def upsert_chunks(
        self, chunks: list[ChunkDocument], embeddings: list[list[float]]
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have equal lengths")
        if not chunks:
            return 0

        # Stable IDs + upsert prevent repeated ingestion from creating duplicate chunks.
        self.collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[
                {
                    "source": chunk.source,
                    "page": chunk.page,
                    "quarter": chunk.quarter,
                    "chunk_index": chunk.chunk_index,
                }
                for chunk in chunks
            ],
        )
        return len(chunks)

    def count(self) -> int:
        return self.collection.count()

    def query(self, query_embedding: list[float], top_k: int = 4) -> list[RetrievedChunk]:
        if self.count() == 0:
            return []
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.count()),
            include=["documents", "metadatas", "distances"],
        )
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        retrieved: list[RetrievedChunk] = []
        for text, metadata, distance in zip(documents, metadatas, distances):
            retrieved.append(
                RetrievedChunk(
                    text=text,
                    source=str(metadata["source"]),
                    page=int(metadata["page"]),
                    quarter=str(metadata["quarter"]),
                    distance=float(distance) if distance is not None else None,
                )
            )
        return retrieved
