from __future__ import annotations

from typing import Any
from .text_cleaner import clean_text
from .document_classifier import DocumentClassifier
from .extraction_engine import ExtractionEngine


class MappingEngine:
    def __init__(self) -> None:
        self.classifier = DocumentClassifier()
        self.extraction_engine = ExtractionEngine()

    def map_template_fields(
        self,
        template_content_json: dict[str, Any],
        document_bundle: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Cleans the uploaded texts, classifies the documents, and runs the hybrid extraction engine.
        """
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

        # 3. Create full combined text for global fallback
        full_text = "\n\n".join(classified_docs.values())

        # 4. Walk the template sections and extract fields
        sections = template_content_json.get("sections", [])
        mapped_sections: list[dict[str, Any]] = []

        for section in sections:
            mapped_fields: list[dict[str, Any]] = []
            for field in section.get("fields", []):
                mapped_fields.append(self._map_field(field, classified_docs, full_text))
            mapped_sections.append({
                "name": section.get("name"),
                "fields": mapped_fields,
                "tables": section.get("tables", []),
            })

        return {"sections": mapped_sections}

    def _map_field(
        self,
        field: dict[str, Any],
        classified_docs: dict[str, str],
        full_text: str,
    ) -> dict[str, Any]:
        ext_res = self.extraction_engine.extract_field(field, classified_docs, full_text)

        # Recurse for nested groups/fields
        nested_fields = [
            self._map_field(child, classified_docs, full_text)
            for child in field.get("nested_fields", [])
        ]

        result = dict(field)
        result["extracted_value"] = ext_res["value"]
        result["confidence"] = ext_res["confidence"]
        result["needs_review"] = ext_res["needs_review"]

        if nested_fields:
            result["nested_fields"] = nested_fields
        return result