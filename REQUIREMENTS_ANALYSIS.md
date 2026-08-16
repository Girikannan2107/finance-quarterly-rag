# Finance RAG — Requirements Analysis

## Primary source

The primary requirements source is **Assignment 1 — Building a RAG System for Quarterly Financial Reports**. The uploaded master prompt is treated as a detailed implementation interpretation, but it must not override the assignment guide.

## Mandatory requirements

- One listed company and 3–4 consecutive quarterly PDFs.
- Confirm PDFs are machine-readable/selectable; empty extraction must be treated as a scanned/image-based input problem.
- Extract page-by-page and retain filename + page number from the beginning.
- Chunk with recursive character splitting, 800–1200 characters, overlap 100–200 characters.
- Keep filename, page, and quarter on every chunk.
- Prefix source/quarter into text before embedding to reduce wrong-quarter retrieval.
- Use `text-embedding-3-small` for both document chunks and user questions.
- Batch document embeddings and do not re-index on every question.
- Store text, embeddings, and metadata in persistent ChromaDB.
- Chroma must survive application restart.
- Prevent duplicate indexing.
- Start retrieval with `top_k=4`.
- Make retrieved chunks inspectable during debugging.
- Use GPT-4o with strict grounding: only retrieved context, refuse if unsupported.
- Use temperature 0 or 0.2.
- Preserve financial figure, currency/unit, and reporting period.
- Display filename + page number beneath each answer.
- Verify at least three figures manually against the PDFs.
- UI must provide upload, index, ask, answer, and sources; show progress; prevent asking before indexing; keep prior Q&A visible.
- Run all 10 required questions and record failures honestly.
- README must include source links, setup/run instructions, chunking decision, prompt, screenshots, all 10 results, and limitations/failures.
- `.env` must hold the OpenAI key and must be excluded from Git.

## Optional requirement

- FastAPI backend with three endpoints is a **bonus (+15)**, not part of the mandatory core.

## Architecture requirement

`PDFs → Text Extraction → Chunking → Embeddings → ChromaDB → Retrieval → GPT-4o → Answer + Sources`

No agentic workflow or external retrieval is required.

## Input requirements

- PDF quarterly reports for one listed company.
- User question.
- OpenAI API key from environment.

## Output requirements

- Grounded answer or explicit refusal.
- Financial figures with correct unit/currency and period.
- Source filename + page number.
- Debug retrieval data during development.

## Evaluation emphasis

- Ingestion pipeline: 20 marks.
- Persistent Chroma usage: 20 marks.
- Correct answers + source/page traceability: 20 marks.
- Interface and graceful error handling: 15 marks.
- Trap question refusal: 10 marks.
- Code quality, README, repository hygiene: 15 marks.
- Optional FastAPI: +15 marks.

## Security requirements

- API key in `.env` only.
- `.env` in `.gitignore`.
- Do not print keys in logs/screenshots.
- Do not expose stack traces or secrets in the user interface.

## Restrictions

- Do not answer from GPT-4o's pretrained knowledge.
- Do not guess missing facts.
- Do not hallucinate financial numbers.
- Do not silently accept empty/scanned extraction.
- Do not discard page provenance.
- Do not create duplicate Chroma chunks on repeated indexing.
- Do not allow questions before indexing.
- Do not prioritize UI polish over retrieval correctness.

## REQUIREMENT NOT SPECIFIED

The assignment does not specify:

1. **UI framework** — simplest implementation chosen: Streamlit.
2. **Exact quarter-detection algorithm** — implementation first reads clean filenames such as `HCLTech_Q1_FY25.pdf`, then falls back to detecting the quarter-end date from extracted text.
3. **Exact Python PDF library** — implementation chosen: PyPDF.
4. **Exact Chroma distance metric** — cosine is chosen because it is appropriate for text embeddings and provides an interpretable similarity diagnostic.
5. **Deployment platform** — not included.

## Conflicts

No material conflict exists between the assignment guide and the uploaded master prompt. The master prompt adds implementation detail but keeps the same required architecture. FastAPI remains optional because the assignment explicitly marks it as bonus work.
