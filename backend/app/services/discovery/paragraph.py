from __future__ import annotations
import re
from ..candidate_model import Candidate
from .base import BaseDiscoveryStrategy
from .index import DocumentIndex

class ParagraphDiscoveryStrategy(BaseDiscoveryStrategy):
    def discover(self, context: DocumentIndex) -> list[Candidate]:
        candidates = []
        # Generic relational patterns in narrative text
        pattern_rel = re.compile(
            r"\b(belongs\s+to|represented\s+by|resident\s+of|referred\s+to\s+as|dated|amounting\s+to|is\s+a|is\s+the|is|was|bearing|having|registered\s+as|between|leased\s+to|sold\s+to|purchased\s+by)\b",
            re.IGNORECASE
        )

        for idx, line in enumerate(context.lines):
            line_clean = line.strip()
            # Paragraph lines are typically longer
            if len(line_clean) > 40:
                for match in pattern_rel.finditer(line_clean):
                    start, end = match.span()
                    left_text = line_clean[:start].strip()
                    right_text = line_clean[end:].strip()

                    # Clean left text: extract the last 2-3 words as a generic label
                    left_words = left_text.split()
                    if left_words:
                        lbl_left = " ".join(left_words[-3:]).strip(".,;: ")
                    else:
                        lbl_left = ""

                    rel_phrase = match.group(1).strip()
                    if lbl_left:
                        lbl = f"{lbl_left} {rel_phrase}"
                    else:
                        lbl = rel_phrase

                    # Strip leading determiners
                    lbl = re.sub(r"^(the|a|an)\s+", "", lbl, flags=re.IGNORECASE)

                    # Clean right text: extract the first clause (up to punctuation) as candidate value
                    right_parts = re.split(r"[,;:|]", right_text)
                    if right_parts:
                        val = right_parts[0].strip(".,;: ")
                    else:
                        val = right_text.strip(".,;: ")

                    if len(lbl) >= 2 and len(lbl) < 40 and len(val) >= 2 and len(val) < 150:
                        c = Candidate(
                            label=lbl,
                            value=val,
                            source_line=idx + 1,
                            page=1,
                            discovery_strategy="paragraph",
                            ocr_confidence=0.75
                        )
                        sec = context.get_section_for_line(idx + 1)
                        c.section = sec.get("heading")
                        c.parent_heading = sec.get("heading")
                        c.context_window = context.get_context_window(idx + 1)
                        candidates.append(c)
        return candidates
