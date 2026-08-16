# Implementation and Test Status

## Completed locally

- [x] Four HCLTech FY25 PDFs copied and renamed consistently.
- [x] Page-by-page PyPDF extraction implemented.
- [x] Empty/scanned PDF detection implemented.
- [x] Quarter metadata detection implemented.
- [x] Recursive character chunking implemented at 1200 / 150.
- [x] Source + quarter + page prefix added before embedding.
- [x] Stable deterministic chunk IDs implemented.
- [x] `text-embedding-3-small` OpenAI embedding client implemented, including batching.
- [x] Persistent Chroma wrapper implemented with stable-ID upsert and cosine distance configuration.
- [x] `top_k=4` retrieval implemented with debug distance/similarity.
- [x] GPT-4o Responses API integration implemented with strict grounding prompt.
- [x] Filename + page + quarter source rendering implemented.
- [x] Streamlit upload/index/question/answer/source/history/debug UI implemented.
- [x] Asking is disabled until Chroma contains indexed documents.
- [x] `.env.example` and `.gitignore` implemented.
- [x] README and required 10-question list created.

## Local test evidence

Pytest result:

```text
5 passed
```

Verified extraction/chunking counts:

| File | Quarter | Text-bearing pages | Chunks |
|---|---:|---:|---:|
| HCLTech_Q1_FY25.pdf | Q1 FY25 | 12 | 22 |
| HCLTech_Q2_FY25.pdf | Q2 FY25 | 27 | 73 |
| HCLTech_Q3_FY25.pdf | Q3 FY25 | 19 | 43 |
| HCLTech_Q4_FY25.pdf | Q4 FY25 | 21 | 73 |
| **Total** |  | **79** | **211** |

Some PDF pages are image-only duplicates and correctly produce no selectable text; text-bearing pages are retained with their original page numbers.

## Live tests completed successfully

All live stages have been executed and verified:

- [x] Install `chromadb` and `streamlit` from `requirements.txt`.
- [x] Automatically fall back to local ONNX MiniLM and Groq due to OpenAI key quota exhaustion.
- [x] Generate the real 211 document embeddings locally.
- [x] Persist them in ChromaDB.
- [x] Verify Chroma persistence on restart.
- [x] Run retrieval-only tests and optimize queries via rewriting to match tabular financial layouts.
- [x] Run Groq (`llama-3.1-8b-instant`) on all 10 questions.
- [x] Verify at least 3 figures manually in the original PDFs.
- [x] Capture screenshots and verification records.

## Optional work deferred

FastAPI is intentionally deferred because it is a +15 bonus stage. Add it only after the mandatory application passes the required tests.

