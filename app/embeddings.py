from __future__ import annotations

from .config import EMBEDDING_MODEL, USE_OPENAI, require_openai_api_key


class OpenAIEmbedder:
    def __init__(self, model: str = EMBEDDING_MODEL):
        self.model = model
        self.use_openai = USE_OPENAI
        if self.use_openai:
            from openai import OpenAI
            self.client = OpenAI(api_key=require_openai_api_key())
        else:
            from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
            self.local_fn = ONNXMiniLM_L6_V2()

    def embed_texts(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        if not texts:
            return []
        if self.use_openai:
            vectors: list[list[float]] = []
            for start in range(0, len(texts), batch_size):
                batch = texts[start : start + batch_size]
                response = self.client.embeddings.create(model=self.model, input=batch)
                ordered = sorted(response.data, key=lambda item: item.index)
                vectors.extend(item.embedding for item in ordered)
            return vectors
        else:
            return self.local_fn(texts)

    def embed_query(self, question: str) -> list[float]:
        if self.use_openai:
            response = self.client.embeddings.create(model=self.model, input=question)
            return response.data[0].embedding
        else:
            return self.local_fn([question])[0]

