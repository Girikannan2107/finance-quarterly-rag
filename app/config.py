from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "data" / "pdfs"
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "quarterly_financial_reports"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150
TOP_K = 4
TEMPERATURE = 0.0


def is_openai_available() -> bool:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    # The default key has insufficient quota
    if not key or key.startswith("sk-proj-viwBHlCeq7Zm5jpR6"):
        return False
    return True


if is_openai_available():
    EMBEDDING_MODEL = "text-embedding-3-small"
    LLM_MODEL = "gpt-4o"
    USE_OPENAI = True
    TOP_K = 4
else:
    EMBEDDING_MODEL = "local-onnx"
    LLM_MODEL = "llama-3.1-8b-instant"
    USE_OPENAI = False
    TOP_K = 10





def require_openai_api_key() -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Copy .env.example to .env and add your key."
        )
    return key


def require_groq_api_key() -> str:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        # Fallback check standard os.environ (set in the parent shell environment)
        key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to your environment or .env file."
        )
    return key

