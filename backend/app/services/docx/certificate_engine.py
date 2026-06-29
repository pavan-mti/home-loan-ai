from __future__ import annotations

from typing import Any
from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from .placeholder_engine import TemplateRenderer


class CertificateEngine:
    @classmethod
    def render_certificate(
        cls,
        document: DocxDocument,
        certificate_text: str | None,
        known_tokens: list[str],
        field_values: dict[str, Any],
    ) -> None:
        if not certificate_text or not certificate_text.strip():
            return

        first_table_elem = document.tables[0]._element if document.tables else None

        lines = certificate_text.splitlines()
        created_paragraphs = []

        for line in lines:
            p = document.add_paragraph()
            if first_table_elem is not None:
                first_table_elem.addprevious(p._element)

            stripped_line = line.strip()
            if not stripped_line:
                created_paragraphs.append(p)
                continue

            # Check special line formatting heuristics
            if "completion certificate" in stripped_line.lower():
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = p.add_run(line)
                r.bold = True
                r.font.size = r.font.size # Keep document default size or style
            elif stripped_line.startswith("To") or stripped_line.startswith("Note:"):
                r = p.add_run(line)
                r.bold = True
            else:
                p.add_run(line)

            created_paragraphs.append(p)

        # Re-use TemplateRenderer on created certificate paragraphs to expand all {{placeholders}}
        for p in created_paragraphs:
            TemplateRenderer.render_paragraph(p, known_tokens, field_values)
