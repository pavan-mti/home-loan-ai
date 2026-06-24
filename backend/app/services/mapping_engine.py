from __future__ import annotations

from typing import Any
from .text_cleaner import clean_text
from .document_classifier import DocumentClassifier
from .extraction_engine import ExtractionEngine


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

def get_canonical_key(field_name: str) -> str:
    if not field_name:
        return ""
    if field_name in FIELD_MAPPING:
        return FIELD_MAPPING[field_name]
    
    fn_lower = field_name.lower()
    for k, v in FIELD_MAPPING.items():
        if k.lower() == fn_lower:
            return v
            
    try:
        from .template_service import map_display_name_to_canonical
        canon = map_display_name_to_canonical(field_name)
        if canon:
            return canon
    except Exception:
        pass
    return field_name


class MappingEngine:
    def __init__(self) -> None:
        self.classifier = DocumentClassifier()
        self.extraction_engine = ExtractionEngine()

    def map_template_fields(
        self,
        template_content_json: dict[str, Any],
        document_bundle: dict[str, dict[str, Any]],
        extracted_results: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """
        Cleans the uploaded texts, classifies the documents, and runs the hybrid extraction engine.
        """
        if extracted_results is None:
            extracted_results = {}

        # 1. Clean the text of all files in the bundle
        cleaned_bundle: dict[str, dict[str, Any]] = {}
        for source_name, data in document_bundle.items():
            raw_text = data.get("text", "")
            cleaned_text = clean_text(raw_text)
            cleaned_bundle[source_name] = {
                "file_name": data.get("file_name"),
                "file_path": data.get("file_path"),
                "text": cleaned_text,
            }

        # 2. Classify the cleaned documents
        classified_docs = self.classifier.classify_bundle(cleaned_bundle)
        print(f"[MappingEngine] Document classification results:")
        if classified_docs:
            for doc_type, text in classified_docs.items():
                print(f"  -> {doc_type}: {len(text)} chars")
        else:
            print("  -> No documents could be classified (all will use full_text fallback)")

        # 3. Create full combined text for global fallback
        full_text = "\n\n".join(classified_docs.values())
        print(f"[MappingEngine] Combined full_text length: {len(full_text)} chars")

        # 4. Walk the template sections and extract fields
        sections = template_content_json.get("sections", [])
        mapped_sections: list[dict[str, Any]] = []
        total_fields = 0
        extracted_fields = 0

        for section in sections:
            mapped_fields: list[dict[str, Any]] = []
            for field in section.get("fields", []):
                mapped = self._map_field(field, classified_docs, full_text, extracted_results)
                mapped_fields.append(mapped)
                if mapped.get("field_type") != "group":
                    total_fields += 1
                    if mapped.get("extracted_value"):
                        extracted_fields += 1
            mapped_sections.append({
                "name": section.get("name"),
                "fields": mapped_fields,
                "tables": section.get("tables", []),
            })

        print(f"[MappingEngine] Field extraction done: {extracted_fields}/{total_fields} fields have values")
        return {"sections": mapped_sections}

    def _map_field(
        self,
        field: dict[str, Any],
        classified_docs: dict[str, str],
        full_text: str,
        extracted_results: dict[str, Any],
    ) -> dict[str, Any]:
        f_type = field.get("field_type", "AUTO")
        field_code = field.get("field_code", "")
        label = field.get("label", "")

        candidate_val = None
        candidate_conf = 0.0
        candidate_nr = True

        if f_type == "SECTION":
            ext_res = {"value": "", "confidence": None, "needs_review": False}
        elif f_type == "MANUAL":
            ext_res = {"value": "", "confidence": None, "needs_review": False}
        else:
            # AUTO (default)
            # Try to retrieve from pre-extracted results (modular extractors)
            canon_key = get_canonical_key(label)
            canon_code = get_canonical_key(field_code)
            
            ext_data = extracted_results.get(canon_key) or extracted_results.get(canon_code)
            if ext_data:
                candidate_val = ext_data.get("value")
                candidate_conf = ext_data.get("confidence", 0.0) / 100.0 if isinstance(ext_data.get("confidence"), (int, float)) else ext_data.get("confidence", 0.0)
                candidate_nr = ext_data.get("needs_review")
                if candidate_nr is None:
                    candidate_nr = True if candidate_conf < 0.7 else False
                
            if candidate_val:
                ext_res = {
                    "value": candidate_val,
                    "confidence": candidate_conf,
                    "needs_review": candidate_nr
                }
            else:
                ext_res = self.extraction_engine.extract_field(field, classified_docs, full_text)

            # Log field details: field_name, field_code, field_type, candidate value, final mapped value
            final_mapped_val = ext_res.get("value")
            print(f"[MappingEngine Log] field_name='{label}', field_code='{field_code}', field_type='{f_type}', candidate_val='{candidate_val}', final_mapped_val='{final_mapped_val}'")

        # Recurse for nested groups/fields
        nested_fields = [
            self._map_field(child, classified_docs, full_text, extracted_results)
            for child in field.get("nested_fields", [])
        ]

        result = dict(field)
        result["extracted_value"] = ext_res["value"]
        result["confidence"] = ext_res["confidence"]
        result["needs_review"] = ext_res["needs_review"]

        if nested_fields:
            result["nested_fields"] = nested_fields
        return result