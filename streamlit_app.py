from __future__ import annotations

import streamlit as st

from app.config import TOP_K
from app.rag_pipeline import FinanceRAG

st.set_page_config(page_title="Quarterly Financial Reports RAG", layout="wide")
st.title("Quarterly Financial Reports RAG")
st.caption("Grounded answers from uploaded quarterly financial reports")

if "history" not in st.session_state:
    st.session_state.history = []

try:
    rag = FinanceRAG()
except Exception as exc:
    st.error(str(exc))
    st.stop()

st.subheader("1. Documents")
uploaded_files = st.file_uploader(
    "Upload 3–4 consecutive quarterly financial-report PDFs",
    type=["pdf"],
    accept_multiple_files=True,
)
if uploaded_files:
    st.write("Uploaded files:")
    for uploaded in uploaded_files:
        st.write(f"- {uploaded.name}")

if st.button("Index documents", type="primary", disabled=not uploaded_files):
    try:
        with st.spinner("Extracting, chunking, embedding, and indexing documents..."):
            uploads = [(f.name, f.getvalue()) for f in uploaded_files]
            result = rag.ingest_uploads(uploads)
        st.success(
            f"Indexed {result['files_processed']} files and {result['chunks_created']} chunks. "
            f"Collection now contains {result['collection_count']} chunks."
        )
        st.dataframe(result["details"], use_container_width=True)
    except Exception as exc:
        st.error(f"Indexing failed: {exc}")

st.divider()
st.subheader("2. Ask a question")
st.write(f"Indexed chunks currently available: **{rag.store.count()}**")
top_k = st.number_input("top_k", min_value=1, max_value=10, value=TOP_K, step=1)
question = st.text_input("Question", placeholder="What was the revenue in the latest quarter?")
ask_disabled = not rag.indexed or not question.strip()
if not rag.indexed:
    st.info("Index documents before asking questions.")

if st.button("Ask", disabled=ask_disabled):
    try:
        with st.spinner("Retrieving relevant chunks and generating a grounded answer..."):
            result = rag.ask(question, top_k=int(top_k))
        st.session_state.history.append({"question": question, **result})
    except Exception as exc:
        st.error(f"Question failed: {exc}")

if st.session_state.history:
    st.divider()
    st.subheader("3. Answer history")
    for item in reversed(st.session_state.history):
        with st.container(border=True):
            st.markdown(f"**Question:** {item['question']}")
            st.markdown("**Answer**")
            st.write(item["answer"])
            st.markdown("**Sources**")
            if item["sources"]:
                for source in item["sources"]:
                    st.write(
                        f"- {source['file']} — Page {source['page']} — {source['quarter']}"
                    )
            else:
                st.write("No supporting source was retrieved.")

            with st.expander("Retrieval debug"):
                for i, chunk in enumerate(item["retrieved"], start=1):
                    similarity = (
                        f"{chunk.similarity:.4f}" if chunk.similarity is not None else "N/A"
                    )
                    st.markdown(
                        f"**Chunk {i}** — {chunk.source}, page {chunk.page}, "
                        f"{chunk.quarter}, similarity {similarity}"
                    )
                    st.code(chunk.text)
