from __future__ import annotations

from pathlib import Path
from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches


class HeaderEngine:
    @classmethod
    def replace_header(cls, document: DocxDocument, header_image_path: Path | None) -> None:
        if not header_image_path or not header_image_path.exists() or not header_image_path.is_file():
            return

        image_str = str(header_image_path)
        printable_width = Inches(6.5)

        # 1. Locate existing letterhead region (all paragraphs situated before the first table in the document body)
        header_paragraphs = []
        if document.tables:
            first_table_elem = document.tables[0]._element
            parent_body = first_table_elem.getparent()
            try:
                table_idx = parent_body.index(first_table_elem)
                for p in document.paragraphs:
                    if p._element.getparent() == parent_body:
                        if parent_body.index(p._element) < table_idx:
                            header_paragraphs.append(p)
            except ValueError:
                header_paragraphs = list(document.paragraphs[:1])
        else:
            header_paragraphs = list(document.paragraphs[:1])

        # If no paragraphs exist before the first table, insert one directly before the table
        if not header_paragraphs:
            if document.tables:
                first_table_elem = document.tables[0]._element
                p = document.add_paragraph()
                first_table_elem.addprevious(p._element)
                header_paragraphs = [p]
            elif document.paragraphs:
                header_paragraphs = [document.paragraphs[0]]
            else:
                p = document.add_paragraph()
                header_paragraphs = [p]

        # 2. Reuse existing paragraph objects in letterhead region, clearing old content
        for p in header_paragraphs:
            p.text = ""
            p._element.clear_content()

        # 3. Insert selected header image into the first header paragraph
        target_p = header_paragraphs[0]
        target_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = target_p.add_run()
        r.add_picture(image_str, width=printable_width)

        # Remaining header_paragraphs (if any) stay empty to preserve exact template spacing
