#!/usr/bin/env python3
"""Test Streamlit RAG pipeline without the Streamlit UI."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.rag_pipeline import FinanceRAG
from app.config import DATA_DIR


def test_rag_full_pipeline():
    print("=" * 80)
    print("TESTING FULL RAG PIPELINE (Streamlit-like workflow)")
    print("=" * 80)
    
    # Initialize RAG
    print("\n1. Initialize RAG...")
    rag = FinanceRAG()
    
    if rag.indexed:
        print(f"   ✓ Already indexed with {rag.store.count()} chunks")
    else:
        print("   Indexing documents...")
        pdf_paths = sorted(Path(DATA_DIR).glob("*.pdf"))
        result = rag.ingest_paths(pdf_paths)
        print(f"   ✓ Indexed {result['files_processed']} files, {result['chunks_created']} chunks")
        print(f"   ✓ Collection now has {result['collection_count']} chunks")
    
    # Test retrieval for multiple questions
    test_questions = [
        "What was the total income each quarter?",
        "How did net profit change across the reported quarters?",
        "What was the revenue in the latest quarter?",
        "What did management say about demand?",
    ]
    
    print("\n2. Test retrieval for various questions...")
    
    for question in test_questions:
        print(f"\n   Q: {question}")
        try:
            retrieved = rag.retrieve(question, top_k=4)
            
            if not retrieved:
                print("      ✗ No chunks retrieved")
                continue
            
            print(f"      ✓ Retrieved {len(retrieved)} chunks:")
            
            for chunk in retrieved[:2]:  # Show first 2
                similarity = (1.0 - chunk.distance) if chunk.distance is not None else None
                sim_str = f"{similarity:.3f}" if similarity is not None else "N/A"
                text_preview = chunk.text[:80].replace("\n", " ")
                print(f"         - {chunk.source} p.{chunk.page}, sim={sim_str}")
                
        except Exception as e:
            print(f"      ✗ Error: {e}")
    
    # Test ask without LLM (just retrieval part)
    print("\n3. Test ask function (without LLM answer)...")
    
    question = "What was the total income each quarter?"
    print(f"\n   Q: {question}")
    
    try:
        retrieved = rag.retrieve(question, top_k=4)
        
        if not retrieved:
            print("   ✗ No chunks retrieved")
        else:
            print(f"   ✓ Retrieved {len(retrieved)} chunks")
            
            # Check if chunks contain relevant keywords
            relevant_found = False
            for chunk in retrieved:
                text_lower = chunk.text.lower()
                if any(kw in text_lower for kw in ["income", "total", "revenue", "profit"]):
                    relevant_found = True
                    break
            
            if relevant_found:
                print("   ✓ Retrieved chunks contain relevant financial keywords")
            else:
                print("   ✗ Retrieved chunks DON'T contain expected keywords")
            
            print("\n   Retrieved context that would be sent to LLM:")
            print("   " + "=" * 76)
            for i, chunk in enumerate(retrieved, start=1):
                print(f"\n   Context {i}: {chunk.source} (Page {chunk.page}, {chunk.quarter})")
                print(f"   Similarity: {(1.0 - chunk.distance) if chunk.distance else 'N/A':.4f}")
                text_preview = chunk.text[:200].replace("\n", " ")
                print(f"   {text_preview}...")
                
    except Exception as e:
        print(f"   ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✓ FULL PIPELINE TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_rag_full_pipeline()
