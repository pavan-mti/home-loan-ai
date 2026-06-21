from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..repositories.template_repository import TemplateRepository
from ..schemas import TemplateCreate, TemplateUpdate
from ..models import TemplateField
from .documents import STORAGE_ROOT, save_upload, flatten_results
from .mapping_engine import MappingEngine
from .ocr_engine import OCREngine
from .report_generator import ReportGenerator
from .template_parser import parse_template_docx, parse_template_pdf


FIELD_MAPPING = {
    "Date of Inspection": "inspection_date",
    "Date of Valuation": "valuation_date",
    "Name of Owner": "owner_name",
    "Survey Number": "survey_number",
    "Village": "village"
}


def map_display_name_to_canonical(display_name: str) -> str | None:
    if not display_name:
        return None
    
    norm_name = display_name.strip()
    
    # 1. Exact match in FIELD_MAPPING
    if norm_name in FIELD_MAPPING:
        return FIELD_MAPPING[norm_name]
    
    # 2. Case-insensitive match in FIELD_MAPPING
    norm_name_lower = norm_name.lower()
    for k, v in FIELD_MAPPING.items():
        if k.lower() == norm_name_lower:
            return v
    
    # 3. Fallback to FIELD_LABELS in base.py
    try:
        from .extractors.base import FIELD_LABELS
        for field_key, labels in FIELD_LABELS.items():
            if any(lbl.strip().lower() == norm_name_lower for lbl in labels):
                return field_key
    except Exception:
        pass
    
    # 4. Fallback to slugified format
    import re
    slug = re.sub(r"[^a-z0-9]+", "_", norm_name_lower).strip("_")
    return slug if slug else None


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
        
        # 1. Extract placeholders and validate
        from .template_field_extractor import extract_template_fields
        placeholders = extract_template_fields(saved_path)
        if not placeholders:
            try:
                saved_path.unlink()
            except Exception:
                pass
            raise ValueError("No template placeholders detected")
            
        parsed_content = parse_template_docx(saved_path)
        storage_url = f"/storage/{saved_path.relative_to(STORAGE_ROOT).as_posix()}"
        template = self.repository.create_template(
            template_key_id=template_key_id,
            template_name=template_name,
            template_bank=template_bank,
            template_content_json=parsed_content,
            original_docx_url=storage_url,
        )
        
        # 2. Insert rows into template_fields
        for idx, field_name in enumerate(placeholders, start=1):
            tf = TemplateField(
                template_id=template.template_id,
                field_name=field_name,
                display_order=idx
            )
            self.repository.db.add(tf)
        self.repository.db.commit()
        
        # 3. Print debug logs
        print(f"Template uploaded: {template_name}\n")
        print("Detected placeholders:")
        for idx, field_name in enumerate(placeholders, start=1):
            print(f"{idx}. {field_name}")
        print(f"\nInserted {len(placeholders)} template fields")
        
        return template.to_dict()

    def import_template(
        self,
        *,
        template_key_id: str,
        template_name: str,
        template_bank: str,
        upload: UploadFile,
    ) -> dict[str, Any]:
        saved_path = save_upload(upload, "templates")
        suffix = saved_path.suffix.lower()
        
        placeholders = []
        if suffix == ".docx":
            from .template_field_extractor import extract_template_fields
            placeholders = extract_template_fields(saved_path)
            if not placeholders:
                try:
                    saved_path.unlink()
                except Exception:
                    pass
                raise ValueError("No template placeholders detected")
                
        if suffix == ".pdf":
            parsed_content = parse_template_pdf(saved_path)
        else:
            parsed_content = parse_template_docx(saved_path)
            
        storage_url = f"/storage/{saved_path.relative_to(STORAGE_ROOT).as_posix()}"
        template = self.repository.create_template(
            template_key_id=template_key_id,
            template_name=template_name,
            template_bank=template_bank,
            template_content_json=parsed_content,
            original_docx_url=storage_url,
        )
        
        if placeholders:
            for idx, field_name in enumerate(placeholders, start=1):
                tf = TemplateField(
                    template_id=template.template_id,
                    field_name=field_name,
                    display_order=idx
                )
                self.repository.db.add(tf)
            self.repository.db.commit()
            
            # Print debug logs
            print(f"Template uploaded: {template_name}\n")
            print("Detected placeholders:")
            for idx, field_name in enumerate(placeholders, start=1):
                print(f"{idx}. {field_name}")
            print(f"\nInserted {len(placeholders)} template fields")
            
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
        updated = self.repository.update_template(template, **payload.model_dump(exclude_unset=True))
        return updated.to_dict()

    def delete_template(self, template_id: int) -> bool:
        template = self.repository.get_template(template_id)
        if template is None:
            return False
            
        self.delete_template_fields(template_id)
        
        if template.original_docx_url:
            url_path = template.original_docx_url.removeprefix("/storage/")
            file_path = STORAGE_ROOT / url_path
            if file_path.exists() and file_path.is_file():
                try:
                    file_path.unlink()
                except Exception:
                    pass
        self.repository.delete_template(template)
        return True

    def get_template_fields(self, template_id: int, as_strings: bool = False) -> list[str] | list[dict[str, Any]]:
        fields = (
            self.repository.db.query(TemplateField)
            .filter(TemplateField.template_id == template_id)
            .order_by(TemplateField.display_order.asc())
            .all()
        )
        if as_strings:
            return [f.field_name for f in fields]
        return [
            {
                "id": f.id,
                "field_name": f.field_name,
                "display_order": f.display_order
            }
            for f in fields
        ]

    def get_template_required_fields(self, template_id: int) -> list[str]:
        field_names = self.get_template_fields(template_id, as_strings=True)
        required_fields = []

        for name in field_names:
            canonical = map_display_name_to_canonical(name)
            if canonical and canonical not in required_fields:
                required_fields.append(canonical)


        return required_fields


    def delete_template_fields(self, template_id: int) -> None:
        self.repository.db.query(TemplateField).filter(TemplateField.template_id == template_id).delete()
        self.repository.db.commit()

    def refresh_template_fields(self, template_id: int) -> list[dict[str, Any]]:
        template = self.repository.get_template(template_id)
        if template is None:
            raise ValueError("Template not found")
        
        if not template.original_docx_url:
            raise ValueError("No template placeholders detected")
            
        url_path = template.original_docx_url.removeprefix("/storage/")
        file_path = STORAGE_ROOT / url_path
        
        if not file_path.exists() or not file_path.is_file():
            raise ValueError("No template placeholders detected")
            
        from .template_field_extractor import extract_template_fields
        placeholders = extract_template_fields(file_path)
        if not placeholders:
            raise ValueError("No template placeholders detected")
            
        # Delete old fields
        self.delete_template_fields(template_id)
        
        # Insert new fields
        for idx, field_name in enumerate(placeholders, start=1):
            tf = TemplateField(
                template_id=template_id,
                field_name=field_name,
                display_order=idx
            )
            self.repository.db.add(tf)
        self.repository.db.commit()
        
        # Print debug log
        print(f"Template uploaded: {template.template_name}\n")
        print("Detected placeholders:")
        for idx, field_name in enumerate(placeholders, start=1):
            print(f"{idx}. {field_name}")
        print(f"\nInserted {len(placeholders)} template fields")
        
        return self.get_template_fields(template_id)

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
        
        from .report_generator import RenderableValue
        
        flat_values = flatten_results(field_values)
        master_dict = {}
        for k, v in flat_values.items():
            master_dict[k] = RenderableValue(v, 1.0, False)

        output_path = STORAGE_ROOT / "reports" / output_name
        return self.report_generator.generate_docx(template.original_docx_url, master_dict, output_path)
