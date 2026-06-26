from __future__ import annotations
from ..candidate_model import Candidate
from .base import BaseDiscoveryStrategy
from .index import DocumentIndex

class KeyValueDiscoveryStrategy(BaseDiscoveryStrategy):
    def discover(self, context: DocumentIndex) -> list[Candidate]:
        candidates = []
        for kv in context.key_values:
            c = Candidate(
                label=kv["label"],
                value=kv["value"],
                source_line=kv["line_num"],
                page=1,
                discovery_strategy="key_value",
                ocr_confidence=0.95 if kv["type"] == "same_line" else 0.90
            )
            # Attach section context
            sec = context.get_section_for_line(kv["line_num"])
            c.section = sec.get("heading")
            c.parent_heading = sec.get("heading")
            c.context_window = context.get_context_window(kv["line_num"])
            candidates.append(c)
        return candidates
