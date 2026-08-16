from __future__ import annotations

from openai import OpenAI

from .config import LLM_MODEL, TEMPERATURE, USE_OPENAI, require_openai_api_key, require_groq_api_key
from .prompts import SYSTEM_PROMPT, build_user_input


class GroundedLLM:
    def __init__(self, model: str = LLM_MODEL):
        self.model = model
        if USE_OPENAI:
            self.client = OpenAI(api_key=require_openai_api_key())
        else:
            self.client = OpenAI(
                api_key=require_groq_api_key(),
                base_url="https://api.groq.com/openai/v1",
            )

    def answer(self, question: str, context: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_input(question, context)},
            ],
            temperature=TEMPERATURE,
        )
        return response.choices[0].message.content.strip()

