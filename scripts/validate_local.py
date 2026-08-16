from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.chunker import chunk_pages
from app.config import CHUNK_OVERLAP, CHUNK_SIZE, DATA_DIR
from app.pdf_loader import extract_pdf


def main() -> None:
    print(f"Chunk configuration: size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP}\n")
    total_chunks = 0
    for path in sorted(Path(DATA_DIR).glob("*.pdf")):
        pages = extract_pdf(path)
        chunks = chunk_pages(pages, CHUNK_SIZE, CHUNK_OVERLAP)
        total_chunks += len(chunks)
        print(
            f"{path.name}: quarter={pages[0].quarter}, "
            f"text_pages={len(pages)}, chunks={len(chunks)}, "
            f"first_sample={pages[0].text[:100]!r}"
        )
    print(f"\nTotal chunks: {total_chunks}")


if __name__ == "__main__":
    main()
