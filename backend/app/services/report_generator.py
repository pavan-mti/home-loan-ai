from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any
from docxtpl import DocxTemplate

from .documents import STORAGE_ROOT


class RenderableValue(dict):
    """
    Subclass of dict to represent fields with confidence scores.
    Allows JSON serialization of value/confidence/needs_review as dict elements,
    while overriding __str__ to display as the raw string value when rendered by docxtpl.
    """
    def __init__(self, value: Any, confidence: float, needs_review: bool = False) -> None:
        super().__init__(value=value, confidence=confidence, needs_review=needs_review)

    @property
    def value(self) -> Any:
        return self["value"]

    @property
    def confidence(self) -> float:
        return self["confidence"]

    @property
    def needs_review(self) -> bool:
        return self["needs_review"]

    def __str__(self) -> str:
        return str(self.value) if self.value is not None else ""


class ReportGenerator:
    def generate_docx(
        self,
        template_path: str | None,
        master_dict: dict[str, Any],
        output_path: Path,
    ) -> Path:
        resolved_template_path = self._resolve_template_path(template_path)
        if resolved_template_path is None:
            raise ValueError("original_docx_url is required to generate a template-preserving report")

        # Load standard template using docxtpl
        doc = DocxTemplate(str(resolved_template_path))

        # Render placeholder context
        doc.render(master_dict)

        final_output_path = self._resolve_output_path(output_path)
        final_output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(final_output_path))
        return final_output_path

    def _resolve_template_path(self, template_path: str | None) -> Path | None:
        if not template_path:
            return None
        if template_path.startswith("/storage/"):
            return STORAGE_ROOT / template_path.removeprefix("/storage/")
        return Path(template_path)

    def _resolve_output_path(self, output_path: Path) -> Path:
        if output_path.parent.name == "generated_reports":
            return output_path

        report_id = output_path.stem or uuid.uuid4().hex
        return STORAGE_ROOT / "generated_reports" / f"{report_id}.docx"