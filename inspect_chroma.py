#!/usr/bin/env python3
"""Debug script to inspect ChromaDB contents without LLM."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.vector_store import ChromaStore
from app.embeddings import OpenAIEmbedder


def main():
    print("=" * 80)
    print("CHROMADB INSPECTION")
    print("=" * 80)
    
    # Initialize store
    store = ChromaStore()
    embedder = OpenAIEmbedder()
    
    print(f"\n✓ ChromaDB opened")
    print(f"  Total chunks: {store.count()}")
    
    if store.count() == 0:
        print("  No documents in database")
        return
    
    # Get some metadata about what's stored
    result = store.collection.get(include=["metadatas"])
    metadatas = result.get("metadatas", [])
    
    if metadatas:
        # Collect stats
        quarters = {}
        sources = {}
        pages = {}
        
        for meta in metadatas:
            q = meta.get("quarter", "unknown")
            s = meta.get("source", "unknown")
            p = meta.get("page", 0)
            
            quarters[q] = quarters.get(q, 0) + 1
            sources[s] = sources.get(s, 0) + 1
            page_key = (s, p)
            pages[page_key] = pages.get(page_key, 0) + 1
        
        print("\n  Quarters represented:")
        for q in sorted(quarters.keys()):
            print(f"    {q}: {quarters[q]} chunks")
        
        print("\n  Files:")
        for s in sorted(sources.keys()):
            print(f"    {s}: {sources[s]} chunks")
    
    # Now test retrieval with problematic question
    print("\n" + "=" * 80)
    print("RETRIEVAL TEST")
    print("=" * 80)
    
    question = "What was the total income each quarter?"
    print(f"\nQuestion: {question}")
    
    try:
        query_embedding = embedder.embed_query(question)
        print(f"✓ Query embedding created (dimension: {len(query_embedding)})")
    except Exception as e:
        print(f"✗ Failed to create embedding: {e}")
        return
    
    try:
        retrieved = store.query(query_embedding, top_k=4)
        print(f"✓ Retrieved {len(retrieved)} chunks:")
        
        for i, chunk in enumerate(retrieved, start=1):
            similarity = (1.0 - chunk.distance) if chunk.distance is not None else None
            print(f"\n  [{i}] {chunk.source}, Page {chunk.page}, {chunk.quarter}")
            print(f"      Distance: {chunk.distance:.4f}, Similarity: {similarity:.4f if similarity else 'N/A'}")
            text_preview = chunk.text[:200].replace("\n", " ")
            print(f"      Text: {text_preview}...")
            
            # Check if it contains relevant keywords
            has_total = "total" in chunk.text.lower()
            has_income = "income" in chunk.text.lower()
            has_revenue = "revenue" in chunk.text.lower()
            has_profit = "profit" in chunk.text.lower()
            
            keywords = []
            if has_total:
                keywords.append("total")
            if has_income:
                keywords.append("income")
            if has_revenue:
                keywords.append("revenue")
            if has_profit:
                keywords.append("profit")
            
            if keywords:
                print(f"      Keywords: {', '.join(keywords)}")
            else:
                print(f"      Keywords: NONE - likely irrelevant!")
            
    except Exception as e:
        print(f"✗ Retrieval failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
