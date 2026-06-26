from __future__ import annotations
import re
from ..candidate_model import Candidate
from .base import BaseDiscoveryStrategy
from .index import DocumentIndex

class NearbyLabelDiscoveryStrategy(BaseDiscoveryStrategy):
    def discover(self, context: DocumentIndex) -> list[Candidate]:
        candidates = []
        # Matches Title Case key/label of 1-3 words followed by a space and alphanumeric value
        pattern_adj = re.compile(r"^([A-Z][a-zA-Z0-9_]+(?:\s+[A-Z][a-zA-Z0-9_]+){0,2})\s+([A-Za-z0-9/\-.,\s()]{2,})$")

        for idx, line in enumerate(context.lines):
            line_clean = line.strip()
            # 1. Horizontal adjacency without separators
            match = pattern_adj.match(line_clean)
            if match:
                lbl = match.group(1).strip()
                val = match.group(2).strip()
                if len(lbl) >= 2 and len(val) >= 2:
                    c = Candidate(
                        label=lbl,
                        value=val,
                        source_line=idx + 1,
                        page=1,
                        discovery_strategy="nearby_label",
                        ocr_confidence=0.85
                    )
                    sec = context.get_section_for_line(idx + 1)
                    c.section = sec.get("heading")
                    c.parent_heading = sec.get("heading")
                    c.context_window = context.get_context_window(idx + 1)
                    candidates.append(c)

            # 2. Vertical/multiline adjacency: short Title Case label line followed by value line
            if idx + 1 < len(context.lines):
                next_line = context.lines[idx + 1].strip()
                if (2 <= len(line_clean) < 30 and 
                    line_clean.replace(" ", "").isalpha() and 
                    line_clean[0].isupper()):
                    if next_line and len(next_line) >= 2 and len(next_line) < 150:
                        c = Candidate(
                            label=line_clean,
                            value=next_line,
                            source_line=idx + 1,
                            page=1,
                            discovery_strategy="nearby_label",
                            ocr_confidence=0.80
                        )
                        sec = context.get_section_for_line(idx + 1)
                        c.section = sec.get("heading")
                        c.parent_heading = sec.get("heading")
                        c.context_window = context.get_context_window(idx + 1)
                        candidates.append(c)
        return candidates
