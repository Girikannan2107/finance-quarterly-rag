# Quarterly Financial Reports RAG — HCLTech FY2024–25

A Retrieval-Augmented Generation application for asking grounded questions over four consecutive HCLTech quarterly financial-result PDFs.

## Objective

Build the assignment pipeline exactly as required:

`PDFs → Text Extraction → Chunking → text-embedding-3-small → ChromaDB → Retrieval → GPT-4o → Answer + Sources`

The priority is correct retrieval, grounded answers, and traceable source pages rather than UI polish.

## Dataset

| Quarter | File | Period end |
|---|---|---|
| Q1 FY25 | `HCLTech_Q1_FY25.pdf` | 30 June 2024 |
| Q2 FY25 | `HCLTech_Q2_FY25.pdf` | 30 September 2024 |
| Q3 FY25 | `HCLTech_Q3_FY25.pdf` | 31 December 2024 |
| Q4 FY25 | `HCLTech_Q4_FY25.pdf` | 31 March 2025 |

Official HCLTech source PDFs:

- Q1: https://www.hcltech.com/sites/default/files/documents/investor-reports/Audited-Financial-Results-for-the-quarter-ended-June-30-2024.pdf
- Q2: https://www.hcltech.com/sites/default/files/documents/investor-reports/audited-financial-results-for-the-quarter-ended-september-30-2024.pdf
- Q3: https://www.hcltech.com/sites/default/files/documents/investor-reports/Audited-Financial-Results-for-the-quarter-ended-December-31-2024_0.pdf
- Q4: https://www.hcltech.com/sites/default/files/documents/investor-reports/Audited-Financial-Results-for-the-quarter-and-year-ended-March-31-2025.pdf
- Financial results index: https://www.hcltech.com/en-us/investor-relations/financial-results

## Architecture

```text
Quarterly PDFs
     ↓
PyPDF text extraction (one page at a time)
     ↓
Text + metadata: filename, page, quarter
     ↓
Recursive character chunking
chunk_size=1200, overlap=150
     ↓
OpenAI text-embedding-3-small
     ↓
Persistent ChromaDB collection (cosine distance)
     ↓
Question embedding with the SAME embedding model
     ↓
Top-k retrieval (default top_k=4)
     ↓
Retrieved chunks only
     ↓
GPT-4o, temperature=0, strict grounding prompt
     ↓
Answer + filename/page sources
```

## Chunking decision

- **Chunk size:** 1200 characters
- **Overlap:** 150 characters
- Both values are inside the assignment ranges (800–1200 and 100–200).
- The upper-end chunk size was chosen because financial PDFs contain dense tables; larger chunks are more likely to keep a row/heading/value together.
- Each chunk remains tied to a single PDF page so page citations remain exact.
- Before embedding, the chunk is prefixed with source, quarter, and page. This reduces wrong-quarter retrieval when multiple reports contain nearly identical wording.

## Metadata

Every stored chunk includes:

```python
{
    "source": "HCLTech_Q4_FY25.pdf",
    "page": 2,
    "quarter": "Q4 FY25",
    "chunk_index": 0
}
```

## Duplicate-indexing prevention

Chunk IDs are deterministic from `source + page + chunk_position`. Chroma uses `upsert`, so re-indexing the same PDF/chunk replaces the existing record instead of blindly adding another copy.

## Grounding prompt

The model is instructed to use only retrieved context, preserve exact financial figures/currency/units/reporting periods, refuse unsupported questions, avoid outside knowledge, and avoid fabricated citations or investment advice. See `app/prompts.py`.

## Setup

Python 3.10+ is required by the assignment.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env`:

```bash
copy .env.example .env
```

On macOS/Linux use `cp .env.example .env`.

Then put your API key in `.env`:

```text
OPENAI_API_KEY=...
```

Never commit `.env`.

## Local validation before using the API

```bash
python scripts/validate_local.py
pytest -q
```

This verifies PDF extraction, quarter detection, chunking, metadata, and deterministic IDs without making OpenAI API calls.

## Run the UI

```bash
streamlit run streamlit_app.py
```

The interface includes:

- multiple-PDF upload
- uploaded-file list
- explicit Index button
- indexing spinner and file/chunk counts
- question box and Ask button
- questions disabled until Chroma contains indexed chunks
- answer + filename/page/quarter sources
- answer history
- retrieval debug view with retrieved chunks and cosine similarity

## Retrieval-first testing

Before judging an LLM answer, inspect the retrieved chunks. Start with `top_k=4`. If a question retrieves the wrong quarter, first inspect source/quarter prefixes and metadata. If retrieval remains weak, test `top_k=5` or `6` only after inspecting the chunks.

## Required 10 questions

1. Revenue in the latest quarter
2. Net profit compared across quarters
3. Year-on-year revenue comparison
4. Management commentary on demand
5. Fastest-growing segment
6. Operating margin trend
7. Dividend declared
8. Risks and headwinds
9. Three-line summary
10. Trap question — must be refused

The exact test prompts are in `tests/required_questions.txt`.

## Manual verification table

Fill this after running the live system:

| # | Question | App answer correct? | Retrieved sources/pages | Manual PDF check | Notes |
|---|---|---|---|---|---|
| 1 | Revenue in latest quarter |  |  |  |  |
| 2 | Net profit across quarters |  |  |  |  |
| 3 | YoY revenue |  |  |  |  |
| 4 | Demand commentary |  |  |  |  |
| 5 | Fastest-growing segment |  |  |  |  |
| 6 | Operating margin trend |  |  |  |  |
| 7 | Dividend |  |  |  |  |
| 8 | Risks/headwinds |  |  |  |  |
| 9 | Three-line summary |  |  |  |  |
| 10 | Trap/refusal |  |  |  |  |

At least three financial figures should be verified manually against the PDFs.

## Known limitations

1. These HCLTech files are statutory financial-result filings. They contain strong numeric data but limited narrative management commentary, so questions about demand or broad risks may correctly produce a refusal if the retrieved documents do not contain support.
2. PDF table extraction converts visual tables to plain text, so alignment can be imperfect. The 1200-character chunk size is intended to reduce table fragmentation.
3. This is document RAG, not live market data. It must not answer using current prices or outside facts.

## Screenshots

Before submission, add screenshots to `screenshots/` showing:

1. PDF upload and indexing with file/chunk count
2. A correct answer with filename + page source
3. A cross-quarter comparison
4. Trap question correctly refused

## Project structure

```text
finance-rag-hcltech/
├── app/
│   ├── config.py
│   ├── models.py
│   ├── pdf_loader.py
│   ├── chunker.py
│   ├── embeddings.py
│   ├── vector_store.py
│   ├── retriever.py
│   ├── prompts.py
│   ├── llm.py
│   └── rag_pipeline.py
├── data/pdfs/
├── chroma_db/
├── screenshots/
├── scripts/validate_local.py
├── tests/
├── streamlit_app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Optional FastAPI bonus

The FastAPI service has been fully implemented in [api_app.py](file:///c:/Users/girik/Downloads/finance-rag-hcltech/api_app.py).

### Run the API Service

```bash
uvicorn api_app:app --host 127.0.0.1 --port 8000
```

### Endpoints and Testing

#### 1. GET `/stats`
Retrieves vector store statistics, including the total number of chunks and the list of indexed files and quarters.

```bash
curl http://localhost:8000/stats
```

#### 2. POST `/query`
Queries the RAG pipeline with a custom question and optional `top_k` parameter. Returns the grounded answer, unique sources (file/page/quarter), and retrieval details.

```bash
curl -X POST -H "Content-Type: application/json" -d "{\"question\": \"What was the revenue in the latest quarter?\", \"top_k\": 10}" http://localhost:8000/query
```

#### 3. POST `/ingest`
Ingests an uploaded PDF file into the database.

```bash
curl -X POST -F "file=@data/pdfs/HCLTech_Q1_FY25.pdf" http://localhost:8000/ingest
```

