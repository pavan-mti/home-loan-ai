from __future__ import annotations

import re
from pathlib import Path
import docx
from docx.text.paragraph import Paragraph
from docx.table import Table


def extract_template_fields(docx_path: str | Path) -> list[str]:
    """
    Extracts placeholders matching `{field_name}` from paragraphs and table cells
    in visual document order in a DOCX template file. Returns a unique list of
    field names preserving their original order of appearance.
    """
    doc = docx.Document(str(docx_path))
    found_fields: list[str] = []
    seen: set[str] = set()

    # Helper function to extract from text
    def extract_from_text(text: str):
        if not text:
            return
        matches = re.findall(r"\{(.*?)\}", text)
        for m in matches:
            cleaned = m.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                found_fields.append(cleaned)

    # Recursive function to scan a table
    def scan_table(table: Table):
        for row in table.rows:
            for cell in row.cells:
                # Scan block-level elements inside cell in order
                for child in cell._tc:
                    if child.tag.endswith('p'):
                        p = Paragraph(child, cell)
                        extract_from_text(p.text)
                    elif child.tag.endswith('tbl'):
                        t = Table(child, cell)
                        scan_table(t)

    # Scan body elements in order
    for child in doc.element.body:
        if child.tag.endswith('p'):
            p = Paragraph(child, doc)
            extract_from_text(p.text)
        elif child.tag.endswith('tbl'):
            t = Table(child, doc)
            scan_table(t)

    return found_fields
