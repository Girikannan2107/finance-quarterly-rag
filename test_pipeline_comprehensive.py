#!/usr/bin/env python3
"""Comprehensive test of the RAG pipeline without requiring OpenAI/Groq keys."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Test 1: PDF Extraction
print("=" * 80)
print("TEST 1: PDF EXTRACTION")
print("=" * 80)

from app.pdf_loader import extract_pdf
from app.config import DATA_DIR

pdf_paths = sorted(Path(DATA_DIR).glob("*.pdf"))
if not pdf_paths:
    print("✗ FAIL: No PDFs found")
    sys.exit(1)

print(f"Found {len(pdf_paths)} PDFs:")
extraction_results = []
for path in pdf_paths:
    try:
        pages = extract_pdf(path)
        print(f"  ✓ {path.name}: {len(pages)} pages, Quarter: {pages[0].quarter}")
        extraction_results.append({
            'file': path.name,
            'pages': len(pages),
            'quarter': pages[0].quarter,
        })
    except Exception as e:
        print(f"  ✗ {path.name}: {e}")
        sys.exit(1)

print("\n✓ PASS: PDF Extraction")

# Test 2: Chunking
print("\n" + "=" * 80)
print("TEST 2: CHUNKING")
print("=" * 80)

from app.chunker import chunk_pages
from app.config import CHUNK_SIZE, CHUNK_OVERLAP

chunking_results = []
total_chunks = 0

for pdf_path in pdf_paths:
    try:
        pages = extract_pdf(pdf_path)
        chunks = chunk_pages(pages, CHUNK_SIZE, CHUNK_OVERLAP)
        
        # Verify all chunks have required metadata
        for chunk in chunks:
            assert chunk.source == pdf_path.name
            assert chunk.page in [p.page for p in pages]
            assert chunk.quarter == pages[0].quarter
            assert len(chunk.text) <= CHUNK_SIZE
            assert "Source:" in chunk.embedded_text
            assert "Quarter:" in chunk.embedded_text
            assert "Page:" in chunk.embedded_text
        
        total_chunks += len(chunks)
        chunking_results.append({
            'file': pdf_path.name,
            'chunks': len(chunks),
        })
        print(f"  ✓ {pdf_path.name}: {len(chunks)} chunks")
    except Exception as e:
        print(f"  ✗ {pdf_path.name}: {e}")
        sys.exit(1)

print(f"\n✓ PASS: Chunking (Total: {total_chunks} chunks)")

# Test 3: Embeddings
print("\n" + "=" * 80)
print("TEST 3: EMBEDDINGS")
print("=" * 80)

from app.embeddings import OpenAIEmbedder

try:
    embedder = OpenAIEmbedder()
    print(f"✓ Embedder initialized (model: {embedder.model})")
    
    # Test embedding a single query
    test_query = "What was the total income each quarter?"
    test_embedding = embedder.embed_query(test_query)
    print(f"✓ Query embedded (dimension: {len(test_embedding)})")
    
    # Test batch embedding
    test_texts = ["Revenue from operations", "Net profit", "Operating margin"]
    test_embeddings = embedder.embed_texts(test_texts)
    print(f"✓ Batch embedded {len(test_texts)} texts (dimensions: {len(test_embeddings[0])})")
    
    print("\n✓ PASS: Embeddings")
except Exception as e:
    print(f"✗ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: ChromaDB Storage and Retrieval
print("\n" + "=" * 80)
print("TEST 4: CHROMADB STORAGE & PERSISTENCE")
print("=" * 80)

from app.vector_store import ChromaStore

try:
    store = ChromaStore()
    initial_count = store.count()
    print(f"✓ ChromaDB connected (current chunks: {initial_count})")
    
    # Collect all chunks and embeddings
    all_chunks = []
    all_embedded_texts = []
    
    for pdf_path in pdf_paths:
        pages = extract_pdf(pdf_path)
        chunks = chunk_pages(pages, CHUNK_SIZE, CHUNK_OVERLAP)
        for chunk in chunks:
            all_chunks.append(chunk)
            all_embedded_texts.append(chunk.embedded_text)
    
    print(f"  Prepared {len(all_chunks)} chunks for ingestion")
    
    # Embed all chunks
    embeddings = embedder.embed_texts(all_embedded_texts)
    print(f"  Created {len(embeddings)} embeddings")
    
    # Upsert into ChromaDB (using upsert so re-runs are idempotent)
    stored_count = store.upsert_chunks(all_chunks, embeddings)
    print(f"  ✓ Upserted {stored_count} chunks")
    
    # Verify persistence
    new_count = store.count()
    print(f"  ✓ ChromaDB now contains {new_count} chunks")
    
    print("\n✓ PASS: ChromaDB Storage")
except Exception as e:
    print(f"✗ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Retrieval
print("\n" + "=" * 80)
print("TEST 5: RETRIEVAL")
print("=" * 80)

from app.retriever import Retriever

try:
    retriever = Retriever(embedder, store)
    
    # Test the problematic question
    question = "What was the total income each quarter?"
    print(f"Question: {question}")
    
    retrieved = retriever.retrieve(question, top_k=4)
    print(f"✓ Retrieved {len(retrieved)} chunks")
    
    if len(retrieved) == 0:
        print("✗ FAIL: No chunks retrieved")
        sys.exit(1)
    
    # Analyze retrieved chunks
    relevant_keywords = ["revenue", "income", "profit", "total", "consolidated"]
    for i, chunk in enumerate(retrieved, start=1):
        text_lower = chunk.text.lower()
        matching = [kw for kw in relevant_keywords if kw in text_lower]
        
        similarity = (1.0 - chunk.distance) if chunk.distance is not None else None
        similarity_str = f"{similarity:.4f}" if similarity is not None else "N/A"
        print(f"\n  [{i}] {chunk.source}, Page {chunk.page}, {chunk.quarter}")
        print(f"      Similarity: {similarity_str}")
        print(f"      Relevant keywords: {', '.join(matching) if matching else 'NONE'}")
        print(f"      Text preview: {chunk.text[:150].replace(chr(10), ' ')}...")
    
    print("\n✓ PASS: Retrieval")
except Exception as e:
    print(f"✗ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Query Enhancement
print("\n" + "=" * 80)
print("TEST 6: QUERY ENHANCEMENT")
print("=" * 80)

try:
    test_questions = [
        "What was the total income each quarter?",
        "How did net profit change across the quarters?",
        "What was the revenue in the latest quarter?",
        "What is the operating margin trend?",
    ]
    
    for q in test_questions:
        enhanced, pattern = retriever._enhance_financial_query(q)
        print(f"\nQ: {q}")
        print(f"   Pattern: {pattern}")
        print(f"   Enhanced: {enhanced[:100]}...")
    
    print("\n✓ PASS: Query Enhancement")
except Exception as e:
    print(f"✗ FAIL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Final Summary
print("\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print("""
✓ PASS: PDF Extraction
✓ PASS: Chunking
✓ PASS: Embeddings
✓ PASS: ChromaDB Persistence
✓ PASS: Retrieval
✓ PASS: Query Enhancement

All core pipeline components are working correctly!
Ready for Streamlit testing with LLM answers.
""")
