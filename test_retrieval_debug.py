#!/usr/bin/env python3
"""Debug script to test retrieval with problematic question."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import DATA_DIR
from app.rag_pipeline import FinanceRAG
from app.pdf_loader import extract_pdf
from app.chunker import chunk_pages


def main():
    print("=" * 80)
    print("FINANCE RAG - RETRIEVAL DEBUG TEST")
    print("=" * 80)
    
    # First, ingest all PDFs
    print("\n1. INGESTION PHASE")
    print("-" * 80)
    rag = FinanceRAG()
    
    pdf_paths = sorted(Path(DATA_DIR).glob("*.pdf"))
    if not pdf_paths:
        print(f"ERROR: No PDFs found in {DATA_DIR}")
        sys.exit(1)
    
    print(f"Found {len(pdf_paths)} PDFs:")
    for path in pdf_paths:
        print(f"  - {path.name}")
    
    # Check if already indexed
    if rag.store.count() == 0:
        print("\nIndexing documents...")
        try:
            result = rag.ingest_paths(pdf_paths)
            print(f"\n✓ Ingestion complete!")
            print(f"  Files: {result['files_processed']}")
            print(f"  Chunks: {result['chunks_created']}")
            print(f"  Total in DB: {result['collection_count']}")
            for detail in result["details"]:
                print(f"    - {detail['file']}: {detail['chunks']} chunks")
        except Exception as e:
            print(f"✗ Ingestion failed: {e}")
            sys.exit(1)
    else:
        print(f"\n✓ Documents already indexed ({rag.store.count()} chunks)")
    
    # Now test retrieval with problematic question
    print("\n" + "=" * 80)
    print("2. RETRIEVAL TEST")
    print("-" * 80)
    
    question = "What was the total income each quarter?"
    print(f"\nQuestion: {question}")
    
    try:
        retrieved = rag.retrieve(question, top_k=4)
        print(f"\n✓ Retrieved {len(retrieved)} chunks:")
        
        for i, chunk in enumerate(retrieved, start=1):
            similarity = (1.0 - chunk.distance) if chunk.distance is not None else None
            print(f"\n  [{i}] {chunk.source}, Page {chunk.page}, {chunk.quarter}")
            print(f"      Distance: {chunk.distance:.4f}, Similarity: {similarity:.4f if similarity else 'N/A'}")
            print(f"      Text (first 200 chars):")
            text_preview = chunk.text[:200].replace("\n", " ")
            print(f"      {text_preview}...")
            
    except Exception as e:
        print(f"✗ Retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Also test with LLM
    print("\n" + "=" * 80)
    print("3. LLM ANSWER GENERATION")
    print("-" * 80)
    
    try:
        result = rag.ask(question, top_k=4)
        print(f"\nAnswer: {result['answer']}")
        if result['sources']:
            print(f"\nSources:")
            for source in result['sources']:
                print(f"  - {source['file']}, Page {source['page']}, {source['quarter']}")
        else:
            print("No sources retrieved")
    except Exception as e:
        print(f"✗ LLM answer failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Sample chunk inspection
    print("\n" + "=" * 80)
    print("4. SAMPLE CHUNK INSPECTION")
    print("-" * 80)
    print("\nExamining first PDF for financial table keywords:")
    
    pdf_path = pdf_paths[0]
    pages = extract_pdf(pdf_path)
    chunks = chunk_pages(pages)
    
    keywords_to_find = ["total", "revenue", "income", "profit", "consolidated", "quarter"]
    found_chunks = []
    
    for chunk in chunks:
        text_lower = chunk.text.lower()
        matching = [kw for kw in keywords_to_find if kw in text_lower]
        if matching:
            found_chunks.append((chunk, matching))
    
    print(f"\nFound {len(found_chunks)} chunks containing financial keywords")
    print("Sample chunks with 'total' or 'income':")
    
    sample_count = 0
    for chunk, keywords in found_chunks:
        if any(kw in keywords for kw in ["total", "income", "revenue"]):
            print(f"\n  Chunk {chunk.chunk_index}, Page {chunk.page}:")
            print(f"  Keywords: {', '.join(set(keywords))}")
            print(f"  Text: {chunk.text[:150]}...")
            sample_count += 1
            if sample_count >= 3:
                break


if __name__ == "__main__":
    main()
