from __future__ import annotations

from .config import TOP_K
from .embeddings import OpenAIEmbedder
from .models import RetrievedChunk
from .vector_store import ChromaStore


class Retriever:
    def __init__(self, embedder: OpenAIEmbedder, store: ChromaStore):
        self.embedder = embedder
        self.store = store

    def retrieve(self, question: str, top_k: int = TOP_K) -> list[RetrievedChunk]:
        if not question.strip():
            raise ValueError("Question cannot be empty.")
        query_embedding = self.embedder.embed_query(question)
        return self.store.query(query_embedding, top_k=top_k)
