from __future__ import annotations

import re
from typing import Any
from .keyword_extractor import extract_by_keywords
from .regex_extractor import extract_by_regex
from .gemini_service import GeminiService


class ExtractionEngine:
    def __init__(self) -> None:
        self.gemini_service = GeminiService()

    def extract_value(
        self,
        placeholder: str,
        document_text: str
    ) -> dict[str, Any]:
        """
        Extracts a value for a single placeholder string using a hierarchy of search strategies.
        The engine is completely unaware of canonical field names.
        """
        from .placeholder_extractor import extract_placeholder
        return extract_placeholder(placeholder, document_text, self.gemini_service)

    def extract_field(
        self,
        field: dict[str, Any],
        classified_docs: dict[str, str],
        full_text: str,
    ) -> dict[str, Any]:
        """
        Coordinates keyword matching, regex searches, and Gemini fallbacks to extract a field.
        """
        doc_source = (field.get("document_source") or "").upper()
        text_to_search = classified_docs.get(doc_source) or full_text
        placeholder = field.get("label") or field.get("field_code") or ""
        return self.extract_value(placeholder, text_to_search)

    def _get_relevant_chunks(self, text: str, keywords: list[str], label: str) -> str:
        """
        Finds occurrences of keywords or labels and builds a context window around them.
        """
        if not text:
            return ""

        terms = list(keywords)
        if label:
            terms.append(label)

        lines = text.split("\n")
        matching_lines: list[int] = []
        for i, line in enumerate(lines):
            if any(re.search(re.escape(term), line, flags=re.IGNORECASE) for term in terms if term.strip()):
                matching_lines.append(i)

        if not matching_lines:
            # Fallback: return first 100 lines
            return "\n".join(lines[:100])

        # Select window of lines around the matches
        selected_indices: set[int] = set()
        for idx in matching_lines:
            start = max(0, idx - 15)
            end = min(len(lines), idx + 15)
            for j in range(start, end):
                selected_indices.add(j)

        sorted_indices = sorted(list(selected_indices))

        chunks: list[str] = []
        last_idx = -2
        for idx in sorted_indices:
            if idx > last_idx + 1:
                chunks.append("... [gap] ...")
            chunks.append(lines[idx])
            last_idx = idx

        chunk_text = "\n".join(chunks)
        return chunk_text[:8000]