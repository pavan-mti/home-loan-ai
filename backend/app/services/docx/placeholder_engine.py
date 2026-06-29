from __future__ import annotations

import re
from typing import Any
from docx.document import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph


class TemplateRenderer:
    @classmethod
    def render_document(
        cls,
        document: DocxDocument,
        known_tokens: list[str],
        field_values: dict[str, Any],
    ) -> None:
        if not known_tokens:
            return

        # Deduplicate and sort tokens by length descending to avoid partial matches
        sorted_tokens = sorted(list(set(known_tokens)), key=len, reverse=True)

        # 1. Process document body paragraphs
        for p in document.paragraphs:
            cls.render_paragraph(p, sorted_tokens, field_values)

        # 2. Process document body tables
        for table in document.tables:
            cls.render_table(table, sorted_tokens, field_values)

        # 3. Process section headers and footers
        for section in document.sections:
            if section.header:
                for p in section.header.paragraphs:
                    cls.render_paragraph(p, sorted_tokens, field_values)
                for t in section.header.tables:
                    cls.render_table(t, sorted_tokens, field_values)
            if section.footer:
                for p in section.footer.paragraphs:
                    cls.render_paragraph(p, sorted_tokens, field_values)
                for t in section.footer.tables:
                    cls.render_table(t, sorted_tokens, field_values)

    @classmethod
    def render_table(
        cls,
        table: Table,
        known_tokens: list[str],
        field_values: dict[str, Any],
    ) -> None:
        processed_cells = set()
        for row in table.rows:
            for cell in row.cells:
                # Track cell XML element to handle merged cells cleanly without duplicating work
                if cell._tc in processed_cells:
                    continue
                processed_cells.add(cell._tc)

                for p in cell.paragraphs:
                    cls.render_paragraph(p, known_tokens, field_values)
                for nested_table in cell.tables:
                    cls.render_table(nested_table, known_tokens, field_values)

    @classmethod
    def render_paragraph(
        cls,
        paragraph: Paragraph,
        known_tokens: list[str],
        field_values: dict[str, Any],
    ) -> None:
        if not paragraph.runs:
            return

        for token in known_tokens:
            if not token:
                continue

            target_pattern = f"{{{{{token}}}}}"

            # Loop to handle multiple occurrences of the same token in a single paragraph
            while True:
                full_text = ""
                char_map = []
                for run in paragraph.runs:
                    if run.text:
                        for idx, ch in enumerate(run.text):
                            char_map.append((run, idx))
                        full_text += run.text

                if not full_text or target_pattern not in full_text:
                    break

                start_idx = full_text.find(target_pattern)
                if start_idx == -1:
                    break

                end_idx = start_idx + len(target_pattern)
                span_chars = char_map[start_idx:end_idx]
                if not span_chars:
                    break

                # Resolve payload value
                raw_val = field_values.get(token)
                if raw_val is None:
                    # Check fallback slug or label lookups
                    slug_token = re.sub(r"[^a-z0-9]+", "_", token.lower()).strip("_")
                    raw_val = field_values.get(slug_token, "")

                if isinstance(raw_val, dict) and "value" in raw_val:
                    val_str = str(raw_val["value"]) if raw_val["value"] is not None else ""
                else:
                    val_str = str(raw_val) if raw_val is not None else ""

                first_run, first_local = span_chars[0]
                last_run, last_local = span_chars[-1]

                if first_run == last_run:
                    orig = first_run.text
                    first_run.text = orig[:first_local] + val_str + orig[last_local + 1:]
                else:
                    orig_first = first_run.text
                    first_run.text = orig_first[:first_local] + val_str

                    run_slices: dict[Any, list[int]] = {}
                    for r, l_idx in span_chars[1:]:
                        if r not in run_slices:
                            run_slices[r] = []
                        run_slices[r].append(l_idx)

                    for r, indices in run_slices.items():
                        min_i = min(indices)
                        max_i = max(indices)
                        r_text = r.text
                        r.text = r_text[:min_i] + r_text[max_i + 1:]
