from __future__ import annotations
from ..candidate_model import Candidate
from .base import BaseDiscoveryStrategy
from .index import DocumentIndex

class TableDiscoveryStrategy(BaseDiscoveryStrategy):
    def discover(self, context: DocumentIndex) -> list[Candidate]:
        candidates = []
        for table in context.tables:
            if not table:
                continue

            # 1. Vertical extraction: headers at row 0, values at rows 1+
            col_headers = table[0]["parts"]
            if len(table) > 1:
                for row in table[1:]:
                    for col_idx, val in enumerate(row["parts"]):
                        if col_idx < len(col_headers):
                            lbl = col_headers[col_idx].strip()
                            val_strip = val.strip()
                            if len(lbl) >= 2 and len(val_strip) >= 2:
                                c = Candidate(
                                    label=lbl,
                                    value=val_strip,
                                    source_line=row["line_num"],
                                    page=1,
                                    discovery_strategy="table",
                                    ocr_confidence=0.90
                                )
                                sec = context.get_section_for_line(row["line_num"])
                                c.section = sec.get("heading")
                                c.parent_heading = sec.get("heading")
                                c.context_window = context.get_context_window(row["line_num"])
                                candidates.append(c)

            # 2. Horizontal extraction: cell j is label, cell j+1 is value (for every row)
            for row in table:
                parts = row["parts"]
                for j in range(len(parts) - 1):
                    lbl = parts[j].strip()
                    val = parts[j+1].strip()
                    if len(lbl) >= 2 and len(lbl) < 60 and len(val) >= 2 and not val.endswith(":"):
                        c = Candidate(
                            label=lbl,
                            value=val,
                            source_line=row["line_num"],
                            page=1,
                            discovery_strategy="table",
                            ocr_confidence=0.88
                        )
                        sec = context.get_section_for_line(row["line_num"])
                        c.section = sec.get("heading")
                        c.parent_heading = sec.get("heading")
                        c.context_window = context.get_context_window(row["line_num"])
                        candidates.append(c)

        return candidates
