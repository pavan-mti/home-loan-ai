from __future__ import annotations

import re
from typing import Any
from .keyword_extractor import extract_by_keywords
from .regex_extractor import extract_by_regex
from .gemini_service import GeminiService


class ExtractionEngine:
    def __init__(self) -> None:
        self.gemini_service = GeminiService()

    def extract_field(
        self,
        field: dict[str, Any],
        classified_docs: dict[str, str],
        full_text: str,
    ) -> dict[str, Any]:
        """
        Coordinates keyword matching, regex searches, and Gemini fallbacks to extract a field.
        """
        field_code = field.get("field_code", "")
        doc_source = (field.get("document_source") or "").upper()
        keywords = field.get("keywords") or []
        label = field.get("label", "")

        # Select relevant source text
        text_to_search = classified_docs.get(doc_source) or full_text

        value = None
        confidence = 0.0

        # Step 1: Keyword extraction
        if keywords or label:
            search_keywords = list(keywords)
            if label and label not in search_keywords:
                search_keywords.append(label)

            kw_res = extract_by_keywords(text_to_search, search_keywords)
            if kw_res["confidence"] > confidence:
                value = kw_res["value"]
                confidence = kw_res["confidence"]

        # Step 2: Regex extraction (if keyword match is not high confidence)
        if confidence < 0.90:
            reg_res = extract_by_regex(field_code, text_to_search)
            if reg_res["confidence"] > confidence:
                value = reg_res["value"]
                confidence = reg_res["confidence"]

        # Step 3: Gemini Fallback (if confidence is low)
        if confidence < 0.7:
            text_chunk = self._get_relevant_chunks(text_to_search, keywords, label)
            if text_chunk:
                ai_res = self.gemini_service.extract_field_with_gemini(
                    field_code=field_code,
                    label=label,
                    keywords=keywords,
                    text_chunk=text_chunk,
                )
                if ai_res and ai_res.get("value"):
                    value = ai_res["value"]
                    confidence = ai_res.get("confidence", 0.85)

        needs_review = confidence < 0.7

        return {
            "value": value,
            "confidence": confidence,
            "needs_review": needs_review,
        }

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
