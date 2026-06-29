from __future__ import annotations

import re
from typing import Any
from docx.document import Document as DocxDocument


class ValidationEngine:
    @classmethod
    def validate_generation(
        cls,
        template: DocxDocument,
        generated: DocxDocument,
        known_tokens: list[str],
    ) -> None:
        # 1. Structural Benchmark Guards
        cls.verify_structural_benchmark(template, generated)

        # 2. Field Resolution Check for Unresolved Tokens
        cls.verify_unresolved_placeholders(generated, known_tokens)

    @classmethod
    def verify_structural_benchmark(cls, template: DocxDocument, generated: DocxDocument) -> None:
        if len(generated.sections) != len(template.sections):
            raise ValueError(f"Structural Benchmark Mismatch: Section count changed ({len(template.sections)} -> {len(generated.sections)})")

        # Note: Paragraph count can naturally increase when rendering completion certificates or top headers.
        # Strict structural benchmarks enforce section and table geometry preservation.

        if len(generated.tables) != len(template.tables):
            raise ValueError(f"Structural Benchmark Mismatch: Table count changed ({len(template.tables)} -> {len(generated.tables)})")

        # Table rows and cells check
        template_rows = sum(len(t.rows) for t in template.tables)
        generated_rows = sum(len(t.rows) for t in generated.tables)
        if generated_rows != template_rows:
            raise ValueError(f"Structural Benchmark Mismatch: Total row count changed ({template_rows} -> {generated_rows})")

        template_cells = sum(sum(len(r.cells) for r in t.rows) for t in template.tables)
        generated_cells = sum(sum(len(r.cells) for r in t.rows) for t in generated.tables)
        if generated_cells != template_cells:
            raise ValueError(f"Structural Benchmark Mismatch: Total cell count changed ({template_cells} -> {generated_cells})")

    @classmethod
    def verify_unresolved_placeholders(cls, document: DocxDocument, known_tokens: list[str]) -> None:
        # Scan for unresolved double-curly bracket placeholders {{...}}
        pattern = re.compile(r"\{\{([a-zA-Z0-9_\s]+)\}\}")
        unresolved = set()

        def scan_text(text: str) -> None:
            if not text:
                return
            for match in pattern.finditer(text):
                token = match.group(1).strip()
                unresolved.add(token)

        for p in document.paragraphs:
            scan_text(p.text)

        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        scan_text(p.text)

        for section in document.sections:
            if section.header:
                for p in section.header.paragraphs:
                    scan_text(p.text)
            if section.footer:
                for p in section.footer.paragraphs:
                    scan_text(p.text)

        if unresolved:
            print(f"[Validation Warning] Unresolved placeholders detected in document: {list(unresolved)}")
