from __future__ import annotations

import re

from .config import TOP_K
from .embeddings import OpenAIEmbedder
from .models import RetrievedChunk
from .vector_store import ChromaStore


class Retriever:
    def __init__(self, embedder: OpenAIEmbedder, store: ChromaStore):
        self.embedder = embedder
        self.store = store
        self.last_query_debug = None  # Store debug info for retrieval

    def _enhance_financial_query(self, question: str) -> str:
        """
        Enhance financial questions by adding relevant financial keywords.
        This helps the embedding model match financial tables better.
        """
        lower_q = question.lower()
        enhanced = question
        matched_pattern = None
        
        # Map conversational terms to financial statement terms
        financial_mappings = [
            # Income/Revenue terms
            (r"(?:revenue|income|earnings?|sales?)\s+(?:each|every|per|across|all)\s+(?:quarter|period)",
             "Revenue from operations total Consolidated Statement quarter",
             "Revenue per quarter"),
            (r"total\s+(?:revenue|income|earnings?)",
             "Total Revenue from operations Consolidated Statement",
             "Total revenue"),
            (r"(?:what.{0,20}?)?revenue.*?(?:each|every|per|across|all)\s+quarter",
             "Revenue from operations total quarterly Consolidated",
             "Revenue quarterly"),
            
            # Profit/Net Income terms
            (r"(?:profit|net\s+profit|net\s+income|earnings?)\s+(?:change|trend|comparison|across|each)",
             "Net profit comprehensive income Profit for the period quarterly",
             "Net profit trend"),
            (r"net\s+profit",
             "Profit for the period Net profit Consolidated Statement",
             "Net profit"),
            
            # Margin terms
            (r"(?:operating\s+)?margin\s+(?:trend|change|comparison|across)",
             "Operating margin segment results Segment revenues profit margin",
             "Margin trend"),
            (r"margin",
             "Operating margin profit margin EBITDA margin segment",
             "Margin"),
            
            # Year-on-year / Comparison terms
            (r"year(?:\s*[-–]?\s*on(?:\s*[-–]?\s*year|y)?|over\s+year)",
             "Year-on-year YoY comparison previous year March",
             "Year-on-year comparison"),
            
            # Segment terms
            (r"segment.*?(?:growth|revenue|profit|performance)",
             "Segment revenue Segment profit IT services Engineering HCL Software growth",
             "Segment performance"),
            (r"which\s+segment\s+(?:grew|growth)",
             "Segment revenue growth IT services Engineering HCL Software",
             "Segment growth"),
            
            # Quarterly terms
            (r"(?:latest|most\s+recent|current)\s+quarter",
             "latest quarter most recent quarterly results",
             "Latest quarter"),
            
            # Dividend terms
            (r"dividend",
             "dividend declared per share interim final",
             "Dividend"),
        ]
        
        for pattern, replacement, pattern_name in financial_mappings:
            if re.search(pattern, lower_q, re.IGNORECASE):
                enhanced = enhanced + " " + replacement
                matched_pattern = pattern_name
                break
        
        # Always add financial context if not already present
        if not any(term in lower_q for term in ["consolidated", "segment", "quarter", "period"]):
            enhanced = enhanced + " Consolidated Statement quarterly financial results"
        
        return enhanced, matched_pattern

    def retrieve(self, question: str, top_k: int = TOP_K) -> list[RetrievedChunk]:
        if not question.strip():
            raise ValueError("Question cannot be empty.")
        
        # Enhance the query with financial context
        enhanced_question, pattern_matched = self._enhance_financial_query(question)
        
        # Store debug info for later access
        self.last_query_debug = {
            "original_question": question,
            "enhanced_question": enhanced_question,
            "pattern_matched": pattern_matched,
        }
        
        # Embed the enhanced query
        query_embedding = self.embedder.embed_query(enhanced_question)
        
        # Retrieve with the enhanced embedding
        return self.store.query(query_embedding, top_k=top_k)
