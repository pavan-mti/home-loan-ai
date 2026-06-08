from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..repositories.template_repository import TemplateRepository
from ..schemas import TemplateCreate, TemplateUpdate
from .documents import STORAGE_ROOT, save_upload
from .mapping_engine import MappingEngine
from .ocr_engine import OCREngine
from .report_generator import ReportGenerator
from .template_parser import parse_template_docx


class TemplateService:
    def __init__(self, repository: TemplateRepository):
        self.repository = repository
        self.ocr_engine = OCREngine()
        self.mapping_engine = MappingEngine()
        self.report_generator = ReportGenerator()

    def create_template(self, payload: TemplateCreate) -> dict[str, Any]:
        template = self.repository.create_template(
            template_key_id=payload.template_key_id,
            template_name=payload.template_name,
            template_bank=payload.template_bank,
            template_content_json=payload.template_content_json.model_dump(),
            original_docx_url=payload.original_docx_url,
        )
        return template.to_dict()

    def import_docx(
        self,
        *,
        template_key_id: str,
        template_name: str,
        template_bank: str,
        upload: UploadFile,
    ) -> dict[str, Any]:
        saved_path = save_upload(upload, "templates")
        parsed_content = parse_template_docx(saved_path)
        storage_url = f"/storage/{saved_path.relative_to(STORAGE_ROOT).as_posix()}"
        template = self.repository.create_template(
            template_key_id=template_key_id,
            template_name=template_name,
            template_bank=template_bank,
            template_content_json=parsed_content,
            original_docx_url=storage_url,
        )
        return template.to_dict()

    def list_templates(self) -> list[dict[str, Any]]:
        return [template.to_dict() for template in self.repository.list_templates()]

    def get_template(self, template_id: int) -> dict[str, Any] | None:
        template = self.repository.get_template(template_id)
        return template.to_dict() if template else None

    def update_template(self, template_id: int, payload: TemplateUpdate) -> dict[str, Any]:
        template = self.repository.get_template(template_id)
        if template is None:
            return {}
        updated = self.repository.update_template(template, **payload.model_dump(exclude_none=True))
        return updated.to_dict()

    def delete_template(self, template_id: int) -> bool:
        template = self.repository.get_template(template_id)
        if template is None:
            return False
        self.repository.delete_template(template)
        return True

    def map_fields(self, template_id: int, upload_paths: list[Path]) -> dict[str, Any]:
        template = self.repository.get_template(template_id)
        if template is None:
            return {}
        document_bundle = {}
        for upload_path in upload_paths:
            source_name = upload_path.stem.upper()
            document_bundle[source_name] = {
                "file_name": upload_path.name,
                "file_path": str(upload_path),
                "text": self.ocr_engine.extract_from_file(upload_path),
            }
        return self.mapping_engine.map_template_fields(template.template_content_json, document_bundle)

    def generate_report(self, template_id: int, field_values: dict[str, Any], output_name: str = "valuation_report.docx") -> Path:
        template = self.repository.get_template(template_id)
        if template is None:
            raise ValueError("Template not found")
        output_path = STORAGE_ROOT / "reports" / output_name
        return self.report_generator.generate_docx(template.original_docx_url, template.template_content_json, field_values, output_path)