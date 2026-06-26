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
    "Borrower Name": "owner_name",
    "Owner Name": "owner_name",
    "Name of Owner": "owner_name",
    "Name of Owner(s)": "owner_name",
    "Name of Owner(S)": "owner_name",
    "Survey Number": "survey_number",
    "Survey No": "survey_number",
    "Survey No. / Door No.": "survey_number",
    "Village": "village",
    "Door Number": "door_number",
    "Property Address": "property_address",
    "Property Description": "property_description",
    "Date of Inspection": "inspection_date",
    "Date of Valuation": "valuation_date",
    "Purchaser Details": "purchaser_name",
    "Purchaser Name": "purchaser_name",
    "Application / LAN No.": "document_id",
    "Purpose": "valuation_purpose",
    "Date of Visit": "inspection_date",
    "Date of Report": "valuation_date",
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
        from .template_field_extractor import extract_template_labels
        placeholders = extract_template_labels(saved_path)
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
        if placeholders:
            print(placeholders[0])
            print(type(placeholders[0]))
        for idx, field_data in enumerate(placeholders, start=1):
            tf = TemplateField(
                template_id=template.template_id,
                field_name=field_data["field_name"],
                field_type=field_data["field_type"],
                static_value=field_data.get("static_value"),
                display_order=idx
            )
            self.repository.db.add(tf)
        self.repository.db.commit()
        
        # 3. Print debug logs
        print(f"Template uploaded: {template_name}\n")
        print("Detected placeholders:")
        for idx, field_data in enumerate(placeholders, start=1):
            print(f"{idx}. {field_data['field_name']} ({field_data['field_type']})")
        print(f"\nInserted {len(placeholders)} template fields")
        
        return template.to_dict()

    def import_template(
        self,
        *,
        template_key_id: str,
        template_name: str,
        template_bank: str,
        upload: UploadFile,
        header_template_id: int | None = None,
    ) -> dict[str, Any]:
        saved_path = save_upload(upload, "templates")
        suffix = saved_path.suffix.lower()
        print(f"[TemplateService] import_template - saved_path: {saved_path}, suffix: {suffix}")
        
        placeholders = []
        if suffix == ".docx":
            from .template_field_extractor import extract_template_labels
            placeholders = extract_template_labels(saved_path)
            print(f"[TemplateService] import_template - extract_template_labels found placeholders: {placeholders}")
            if not placeholders:
                print(f"[TemplateService] import_template - ERROR: placeholders list is empty!")
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
            print(placeholders[0])
            print(type(placeholders[0]))
            for idx, field_data in enumerate(placeholders, start=1):
                tf = TemplateField(
                    template_id=template.template_id,
                    field_name=field_data["field_name"],
                    field_type=field_data["field_type"],
                    static_value=field_data.get("static_value"),
                    display_order=idx
                )
                self.repository.db.add(tf)
            self.repository.db.commit()
            
            # Print debug logs
            print(f"Template uploaded: {template_name}\n")
            print("Detected placeholders:")
            for idx, field_data in enumerate(placeholders, start=1):
                print(f"{idx}. {field_data['field_name']} ({field_data['field_type']})")
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

    def get_template_fields(self, template_id: int, as_strings: bool = True) -> list[str] | list[dict[str, Any]]:
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
                "display_order": f.display_order,
                "field_type": f.field_type,
                "static_value": f.static_value
            }
            for f in fields
        ]

    def get_template_field_count(self, template_id: int) -> int:
        return self.repository.db.query(TemplateField).filter(TemplateField.template_id == template_id).count()

    def get_template_required_fields(self, template_id: int) -> list[str]:
        fields = (
            self.repository.db.query(TemplateField)
            .filter(TemplateField.template_id == template_id, TemplateField.field_type == "AUTO")
            .order_by(TemplateField.display_order.asc())
            .all()
        )
        return [f.field_name for f in fields]



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
            
        from .template_field_extractor import extract_template_labels
        placeholders = extract_template_labels(file_path)
        if not placeholders:
            raise ValueError("No template placeholders detected")
            
        # Delete old fields
        self.delete_template_fields(template_id)
        
        # Insert new fields
        if placeholders:
            print(placeholders[0])
            print(type(placeholders[0]))
        for idx, field_data in enumerate(placeholders, start=1):
            tf = TemplateField(
                template_id=template_id,
                field_name=field_data["field_name"],
                field_type=field_data["field_type"],
                static_value=field_data.get("static_value"),
                display_order=idx
            )
            self.repository.db.add(tf)
        self.repository.db.commit()
        
        # Print debug log
        print(f"Template uploaded: {template.template_name}\n")
        print("Detected placeholders:")
        for idx, field_data in enumerate(placeholders, start=1):
            print(f"{idx}. {field_data['field_name']} ({field_data['field_type']})")
        print(f"\nInserted {len(placeholders)} template fields")
        
        return self.get_template_fields(template_id, as_strings=False)

    def map_fields(self, template_id: int, upload_paths: list[Path]) -> dict[str, Any]:
        template = self.repository.get_template(template_id)
        if template is None:
            print(f"[TemplateService] ERROR: Template ID {template_id} not found.")
            return {}
        print(f"\n[TemplateService] Starting field mapping for template: '{template.template_name}' (ID={template_id})")
        print(f"[TemplateService] {len(upload_paths)} uploaded file(s) to process.")
        document_bundle = {}
        for i, upload_path in enumerate(upload_paths, start=1):
            source_name = upload_path.stem.upper()
            print(f"[TemplateService] ({i}/{len(upload_paths)}) Extracting text from: {upload_path.name}")
            extracted_text = self.ocr_engine.extract_from_file(upload_path)
            print(f"[TemplateService] ({i}/{len(upload_paths)}) Extracted {len(extracted_text)} characters from {upload_path.name}")
            document_bundle[source_name] = {
                "file_name": upload_path.name,
                "file_path": str(upload_path),
                "text": extracted_text,
            }
        print(f"[TemplateService] All files extracted. Running classification and field mapping...")
        
        from .documents import analyze_document
        required_fields = self.get_template_required_fields(template_id)
        extracted_results = {}
        for upload_path in upload_paths:
            print(f"[TemplateService] Running analyze_document on path: {upload_path}")
            doc_results = analyze_document(upload_path, required_fields)
            print(f"[TemplateService] Extracted dict returned by analyze_document: {doc_results}")
            print("\n===== EXTRACTED RESULTS =====")
            print(extracted_results)
            print("============================\n")
            for res in doc_results:
                placeholder = res.get("label") or res.get("field_name")
                val = res.get("value")
                conf = res.get("confidence", 0)
                if val and placeholder:
                    existing = extracted_results.get(placeholder)
                    if not existing or conf > existing.get("confidence", 0):
                        extracted_results[placeholder] = res

        print("\n========== TEMPLATE CONTENT ==========")
        print(template.template_content_json)
        print("======================================\n")

        # Compatibility adapter: Map placeholder keys to canonical keys for MappingEngine
        import re
        adapted_extracted_results = {}
        for placeholder, res in extracted_results.items():
            canon = res.get("canonical_name")
            if not canon:
                canon = map_display_name_to_canonical(placeholder)
            if not canon:
                canon = re.sub(r"[^a-z0-9]+", "_", placeholder.lower()).strip("_")
            adapted_extracted_results[canon] = res

        result = self.mapping_engine.map_template_fields(
            template.template_content_json,
            document_bundle,
            adapted_extracted_results
        )
        total_sections = len(result.get("sections", []))
        print(f"[TemplateService] Mapping complete. {total_sections} section(s) mapped.\n")
        print(f"[TemplateService] Final map-fields response: {result}")
        return result


    def generate_report(self, template_id: int, field_values: dict[str, Any], output_name: str = "valuation_report.docx", header_image_path: Path | None = None) -> Path:
        template = self.repository.get_template(template_id)
        if template is None:
            raise ValueError("Template not found")
        
        from .report_generator import RenderableValue
        
        flat_values = flatten_results(field_values)
        master_dict = {}
        for k, v in flat_values.items():
            master_dict[k] = RenderableValue(v, 1.0, False)

        output_path = STORAGE_ROOT / "reports" / output_name
        return self.report_generator.generate_docx(
            template.original_docx_url,
            template.template_content_json,
            master_dict,
            output_path,
            header_image_path=header_image_path
        )

    def map_saved_fields(self, template_id: int, saved_values: dict[str, Any]) -> dict[str, Any]:
        template = self.repository.get_template(template_id)
        if template is None:
            return {}
        
        template_content = template.template_content_json or {}
        sections = template_content.get("sections", [])
        mapped_sections = []
        
        def map_field_rec(field: dict[str, Any]) -> dict[str, Any]:
            # Try to find a match in saved_values
            val = None
            field_code = field.get("field_code")
            label = field.get("label")
            
            # Match priority:
            # 1. field_code in saved_values
            if field_code and field_code in saved_values:
                val = saved_values[field_code]
            # 2. map display name of label to canonical
            elif label:
                canonical = map_display_name_to_canonical(label)
                if canonical and canonical in saved_values:
                    val = saved_values[canonical]
                elif label in saved_values:
                    val = saved_values[label]
            
            # Recurse for nested fields
            nested = [map_field_rec(child) for child in field.get("nested_fields", [])]
            
            f_type = field.get("field_type", "AUTO")
            res = dict(field)
            if f_type == "SECTION":
                res["extracted_value"] = ""
                res["confidence"] = None
                res["needs_review"] = False
            elif f_type == "MANUAL":
                res["extracted_value"] = val if val is not None else ""
                res["confidence"] = None
                res["needs_review"] = False
            else: # AUTO
                res["extracted_value"] = val if val is not None else ""
                res["confidence"] = 1.0 if val is not None else 0.0
                res["needs_review"] = False if val is not None else True
                
            if nested:
                res["nested_fields"] = nested
            return res

        for section in sections:
            mapped_fields = []
            for field in section.get("fields", []):
                mapped_fields.append(map_field_rec(field))
            mapped_sections.append({
                "name": section.get("name"),
                "fields": mapped_fields,
                "tables": section.get("tables", []),
            })
            
        return {"sections": mapped_sections}
