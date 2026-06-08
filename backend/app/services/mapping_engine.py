from __future__ import annotations

import re
from typing import Any


class MappingEngine:
    def map_template_fields(self, template_content_json: dict[str, Any], document_bundle: dict[str, dict[str, Any]]) -> dict[str, Any]:
        sections = template_content_json.get("sections", [])
        mapped_sections: list[dict[str, Any]] = []

        for section in sections:
            mapped_fields: list[dict[str, Any]] = []
            for field in section.get("fields", []):
                mapped_fields.append(self._map_field(field, document_bundle))
            mapped_sections.append({"name": section.get("name"), "fields": mapped_fields, "tables": section.get("tables", [])})

        return {"sections": mapped_sections}

    def _map_field(self, field: dict[str, Any], document_bundle: dict[str, dict[str, Any]]) -> dict[str, Any]:
        source_texts = self._select_source_texts(field, document_bundle)
        extracted_value = self._search_texts(field, source_texts)
        nested_fields = [self._map_field(child, document_bundle) for child in field.get("nested_fields", [])]
        result = dict(field)
        result["extracted_value"] = extracted_value
        if nested_fields:
            result["nested_fields"] = nested_fields
        return result

    def _select_source_texts(self, field: dict[str, Any], document_bundle: dict[str, dict[str, Any]]) -> list[str]:
        source = (field.get("document_source") or "").upper()
        texts: list[str] = []
        if source:
            for document_name, payload in document_bundle.items():
                if document_name.upper() == source or source in document_name.upper():
                    texts.append(payload.get("text", ""))
        if not texts:
            texts = [payload.get("text", "") for payload in document_bundle.values()]
        return texts

    def _search_texts(self, field: dict[str, Any], texts: list[str]) -> str | None:
        keywords = field.get("keywords", []) or []
        label = field.get("label", "")
        patterns = [*(keywords or []), label]

        for text in texts:
            if not text:
                continue
            for keyword in patterns:
                if not keyword:
                    continue
                value = self._extract_after_keyword(text, keyword)
                if value:
                    return value
        return field.get("static_value")

    def _extract_after_keyword(self, text: str, keyword: str) -> str | None:
        escaped = re.escape(keyword)
        candidates = [
            rf"{escaped}\s*[:\-]?\s*([A-Za-z0-9,./()'\-& ]{{2,}})",
            rf"{escaped}.*?([A-Z0-9][A-Z0-9,./()'\-& ]{{2,}})",
        ]
        for pattern in candidates:
            match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if match:
                value = re.sub(r"\s+", " ", match.group(1)).strip()
                if value:
                    return value
        return None