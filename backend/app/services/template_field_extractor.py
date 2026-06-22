from __future__ import annotations

from pathlib import Path
from typing import Any

import docx


def extract_template_labels(docx_path: str | Path) -> list[dict[str, Any]]:
    """
    Extracts fields from the first column of tables in a DOCX template file.
    Classifies them as dynamic or static fields following layout heuristics.
    Returns a unique list of field metadata dicts preserving their order of appearance.
    """
    doc = docx.Document(str(docx_path))
    fields: list[dict[str, Any]] = []
    seen: set[str] = set()

    for table in doc.tables:
        for row in table.rows:
            if len(row.cells) < 2:
                continue

            left_cell = row.cells[0].text.strip()
            right_cell = row.cells[1].text.strip()

            # Rule 1: Ignore empty labels
            if not left_cell:
                continue

            # Rule 2: Ignore section headers structurally (repeated left=right rows or merged cells)
            if left_cell == right_cell:
                continue

            # Rule 6: Remove duplicates (preserving first occurrence)
            if left_cell in seen:
                continue
            seen.add(left_cell)

            # Rule 3 & 4: Classify static vs dynamic fields
            # Rows whose right cell is empty or contains instructions/placeholders are dynamic fields.
            is_dynamic = False
            if not right_cell:
                is_dynamic = True
            elif "{" in right_cell or "}" in right_cell:
                is_dynamic = True

            if is_dynamic:
                fields.append({
                    "field_name": left_cell,
                    "field_type": "dynamic",
                    "static_value": None
                })
            else:
                fields.append({
                    "field_name": left_cell,
                    "field_type": "static",
                    "static_value": right_cell
                })

    return fields
