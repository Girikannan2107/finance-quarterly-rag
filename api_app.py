from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag_pipeline import FinanceRAG

app = FastAPI(
    title="Quarterly Financial Reports RAG API",
    description="FastAPI service for document ingestion, persistent vector query, and stats lookup.",
    version="1.0.0",
)

# Instantiate the pipeline
try:
    rag = FinanceRAG()
except Exception as exc:
    print(f"Error initializing FinanceRAG: {exc}")
    rag = None


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = None


class SourceMetadata(BaseModel):
    file: str
    page: int
    quarter: str


class ChunkDetail(BaseModel):
    text: str
    source: str
    page: int
    quarter: str
    similarity: Optional[float] = None


class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceMetadata]
    retrieved: List[ChunkDetail]


@app.post("/ingest")
async def ingest_file(file: UploadFile = File(...)) -> Any:
    if not rag:
        raise HTTPException(status_code=500, detail="FinanceRAG pipeline is not initialized.")
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    try:
        content = await file.read()
        result = rag.ingest_uploads([(file.filename, content)])
        return {
            "message": f"Successfully ingested {file.filename}",
            "chunks_created": result["chunks_created"],
            "collection_count": result["collection_count"],
            "details": result["details"],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/query", response_model=QueryResponse)
def query_rag(request: QueryRequest) -> Any:
    if not rag:
        raise HTTPException(status_code=500, detail="FinanceRAG pipeline is not initialized.")
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        from app.config import TOP_K

        top_k = request.top_k or TOP_K
        result = rag.ask(request.question, top_k=top_k)

        # Format retrieved chunks
        retrieved_list = []
        for chunk in result["retrieved"]:
            retrieved_list.append(
                ChunkDetail(
                    text=chunk.text,
                    source=chunk.source,
                    page=chunk.page,
                    quarter=chunk.quarter,
                    similarity=chunk.similarity,
                )
            )

        return QueryResponse(
            answer=result["answer"],
            sources=[
                SourceMetadata(file=s["file"], page=s["page"], quarter=s["quarter"])
                for s in result["sources"]
            ],
            retrieved=retrieved_list,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/stats")
def get_stats() -> Any:
    if not rag:
        raise HTTPException(status_code=500, detail="FinanceRAG pipeline is not initialized.")
    try:
        count = rag.store.count()
        files = []
        quarters = []
        if count > 0:
            res_get = rag.store.collection.get(include=["metadatas"])
            metadatas = res_get.get("metadatas", [])
            if metadatas:
                files = sorted(list(set(m["source"] for m in metadatas if m and "source" in m)))
                quarters = sorted(
                    list(set(m["quarter"] for m in metadatas if m and "quarter" in m))
                )

        return {
            "total_chunks": count,
            "indexed_files": files,
            "indexed_quarters": quarters,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
