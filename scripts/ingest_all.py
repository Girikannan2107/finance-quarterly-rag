import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import DATA_DIR
from app.rag_pipeline import FinanceRAG


def main() -> None:
    print("Initializing FinanceRAG pipeline...")
    rag = FinanceRAG()

    pdf_paths = sorted(Path(DATA_DIR).glob("*.pdf"))
    if not pdf_paths:
        print(f"Error: No PDF files found in {DATA_DIR}")
        sys.exit(1)

    print(f"Found {len(pdf_paths)} PDF files to ingest:")
    for p in pdf_paths:
        print(f" - {p.name}")

    print("\nIngesting documents (extracting, chunking, embedding, and storing)...")
    try:
        result = rag.ingest_paths(pdf_paths)
        print("\nIngestion completed successfully!")
        print(f"Processed: {result['files_processed']} files")
        print(f"Chunks created: {result['chunks_created']}")
        print(f"Total chunks in database: {result['collection_count']}")
        print("\nDetails:")
        for detail in result["details"]:
            print(
                f" - {detail['file']} ({detail['quarter']}): "
                f"{detail['pages']} pages, {detail['chunks']} chunks"
            )
    except Exception as exc:
        print(f"\nError during ingestion: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
