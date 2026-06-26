from __future__ import annotations
from ..candidate_model import Candidate
from .base import BaseDiscoveryStrategy
from .index import DocumentIndex

class SectionDiscoveryStrategy(BaseDiscoveryStrategy):
    def discover(self, context: DocumentIndex) -> list[Candidate]:
        candidates = []
        for sec in context.sections:
            heading = sec["heading"]
            if not heading or heading == "Document Start":
                continue

            for idx, line in enumerate(sec["lines"]):
                line_clean = line.strip()
                if line_clean == heading:
                    continue
                if line_clean and len(line_clean) >= 2 and len(line_clean) < 150:
                    c = Candidate(
                        label=heading,
                        value=line_clean,
                        source_line=sec["start_line"] + idx,
                        page=1,
                        discovery_strategy="section",
                        ocr_confidence=0.80,
                        section=heading,
                        parent_heading=heading,
                        context_window=context.get_context_window(sec["start_line"] + idx)
                    )
                    candidates.append(c)
        return candidates
