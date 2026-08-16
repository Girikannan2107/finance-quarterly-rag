from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .chunker import chunk_pages
from .config import CHUNK_OVERLAP, CHUNK_SIZE, TOP_K
from .embeddings import OpenAIEmbedder
from .llm import GroundedLLM
from .models import RetrievedChunk
from .pdf_loader import extract_pdf, extract_pdf_bytes
from .retriever import Retriever
from .vector_store import ChromaStore


class FinanceRAG:
    def __init__(self):
        self.embedder = OpenAIEmbedder()
        self.store = ChromaStore()
        self.retriever = Retriever(self.embedder, self.store)
        self._llm = None  # Lazy initialization

    @property
    def llm(self) -> GroundedLLM:
        """Lazily initialize LLM only when needed."""
        if self._llm is None:
            self._llm = GroundedLLM()
        return self._llm

    @property
    def indexed(self) -> bool:
        return self.store.count() > 0

    def ingest_paths(self, paths: Iterable[str | Path]) -> dict:
        all_chunks = []
        files_processed = 0
        details = []
        for path in paths:
            pages = extract_pdf(path)
            chunks = chunk_pages(pages, CHUNK_SIZE, CHUNK_OVERLAP)
            if not chunks:
                raise RuntimeError(f"No chunks produced for {Path(path).name}.")
            all_chunks.extend(chunks)
            files_processed += 1
            details.append(
                {
                    "file": Path(path).name,
                    "quarter": pages[0].quarter,
                    "pages": len(pages),
                    "chunks": len(chunks),
                }
            )

        embeddings = self.embedder.embed_texts([c.embedded_text for c in all_chunks])
        self.store.upsert_chunks(all_chunks, embeddings)
        return {
            "files_processed": files_processed,
            "chunks_created": len(all_chunks),
            "collection_count": self.store.count(),
            "details": details,
        }

    def ingest_uploads(self, uploads: list[tuple[str, bytes]]) -> dict:
        all_chunks = []
        details = []
        for filename, data in uploads:
            pages = extract_pdf_bytes(data, filename)
            chunks = chunk_pages(pages, CHUNK_SIZE, CHUNK_OVERLAP)
            if not chunks:
                raise RuntimeError(f"No chunks produced for {filename}.")
            all_chunks.extend(chunks)
            details.append(
                {
                    "file": filename,
                    "quarter": pages[0].quarter,
                    "pages": len(pages),
                    "chunks": len(chunks),
                }
            )
        embeddings = self.embedder.embed_texts([c.embedded_text for c in all_chunks])
        self.store.upsert_chunks(all_chunks, embeddings)
        return {
            "files_processed": len(uploads),
            "chunks_created": len(all_chunks),
            "collection_count": self.store.count(),
            "details": details,
        }

    def retrieve(self, question: str, top_k: int = TOP_K) -> list[RetrievedChunk]:
        if not self.indexed:
            raise RuntimeError("No documents have been indexed yet.")
        
        # Delegate to retriever, which handles query enhancement
        return self.retriever.retrieve(question, top_k=top_k)



    @staticmethod
    def _context_from_chunks(chunks: list[RetrievedChunk]) -> str:
        blocks = []
        for i, chunk in enumerate(chunks, start=1):
            blocks.append(
                f"[Context {i}]\n"
                f"Source: {chunk.source}\n"
                f"Quarter: {chunk.quarter}\n"
                f"Page: {chunk.page}\n"
                f"Text:\n{chunk.text}"
            )
        return "\n\n".join(blocks)

    def ask(self, question: str, top_k: int = TOP_K) -> dict:
        chunks = self.retrieve(question, top_k=top_k)
        
        # Get query debug info from retriever
        query_debug = getattr(self.retriever, 'last_query_debug', None)
        
        if not chunks:
            return {
                "answer": "I cannot answer this from the uploaded financial reports because the required information is not present in the retrieved context.",
                "sources": [],
                "retrieved": [],
                "query_debug": query_debug,
            }
        context = self._context_from_chunks(chunks)
        answer = self.llm.answer(question, context)
        unique_sources = []
        seen = set()
        for chunk in chunks:
            key = (chunk.source, chunk.page)
            if key not in seen:
                seen.add(key)
                unique_sources.append(
                    {"file": chunk.source, "page": chunk.page, "quarter": chunk.quarter}
                )
        return {
            "answer": answer,
            "sources": unique_sources,
            "retrieved": chunks,
            "query_debug": query_debug,
        }
