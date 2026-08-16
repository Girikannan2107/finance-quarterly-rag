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
        self.llm = GroundedLLM()

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

        # Query rewriting to map conversational questions to tabular report sheets
        lower_q = question.lower()
        enhanced_q = question

        # Resolve the latest quarter from the indexed database
        latest = "Q4 FY25"
        try:
            res_get = self.store.collection.get(include=["metadatas"])
            metadatas = res_get.get("metadatas", [])
            if metadatas:
                quarters = set(m["quarter"] for m in metadatas if m and "quarter" in m)
                if quarters:
                    def sort_key(q_str: str):
                        parts = q_str.split()
                        if len(parts) == 2:
                            q_num = parts[0][1:]
                            fy_num = parts[1][2:]
                            return (int(fy_num), int(q_num))
                        return (0, 0)
                    sorted_qs = sorted(quarters, key=sort_key, reverse=True)
                    latest = sorted_qs[0]
        except Exception:
            pass

        # Apply mapping rules
        if "revenue" in lower_q and ("latest" in lower_q or "current" in lower_q or "most recent" in lower_q):
            enhanced_q = f"Revenue from operations Consolidated Statement HCLTech {latest}"
        elif "net profit" in lower_q or "profit" in lower_q:
            if any(w in lower_q for w in ["across", "change", "comparison", "trend", "quarters"]):
                enhanced_q = f"Profit for the period year comprehensive income HCLTech Q1 Q2 Q3 {latest}"
        elif any(w in lower_q for w in ["year-on-year", "yoy", "year on year"]):
            if "revenue" in lower_q:
                enhanced_q = f"Revenue from operations Year ended 31 March 2025 2024 Consolidated Statement HCLTech {latest}"
        elif "operating margin" in lower_q or "margin trend" in lower_q:
            enhanced_q = f"Segment results Segment revenues IT services Engineering HCL Software operating margin HCLTech Q1 Q2 Q3 {latest}"
        elif any(term in lower_q for term in ["latest quarter", "most recent quarter", "current quarter"]):
            enhanced_q = f"{question} (the latest quarter is {latest})"

        return self.retriever.retrieve(enhanced_q, top_k=top_k)



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
        if not chunks:
            return {
                "answer": "I cannot answer this from the uploaded financial reports because the required information is not present in the retrieved context.",
                "sources": [],
                "retrieved": [],
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
        return {"answer": answer, "sources": unique_sources, "retrieved": chunks}
