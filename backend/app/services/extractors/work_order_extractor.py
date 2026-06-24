from __future__ import annotations
import re
from typing import Any
from .base import BaseExtractor

class WorkOrderExtractor(BaseExtractor):
    def extract(self, text: str, page_results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        req = getattr(self, "required_fields", None)
        permission_number = None
        source_page = None
        ocr_conf = 0.0
        regex_conf = 0.0
        final_conf = 0.0
        
        if req is None or "permission_number" in req:
            clean_text = text.replace("|", " ")
            permission_number = self._extract_permission_number(clean_text)
            
            if permission_number:
                source_page = self._find_source_page_for_line(permission_number, page_results) + 1
                ocr_conf = self._get_ocr_confidence(permission_number, source_page - 1, page_results)
                regex_conf = 0.95
                final_conf = (0.7 * ocr_conf) + (0.3 * regex_conf)
            
        wo_party_name = self.extract_field_pipeline(text, "wo_party_name", page_results)
        return {
            "permission_number": {
                "value": permission_number,
                "source_page": source_page,
                "ocr_confidence": float(ocr_conf),
                "regex_confidence": float(regex_conf),
                "final_confidence": float(final_conf)
            },
            "wo_party_name": wo_party_name
        }

    def _extract_permission_number(self, text: str) -> str | None:
        MONTH_ABBRS = {"jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"}
        
        def is_date_or_stamp(val: str) -> bool:
            val_clean = val.strip().lower()
            if re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", val_clean):
                return True
            if re.search(r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b", val_clean):
                return True
            for m in MONTH_ABBRS:
                if val_clean.startswith(m) and len(val_clean) > len(m):
                    tail = val_clean[len(m):]
                    if re.match(r"^[-/.\s]\d+", tail):
                        return True
            return False

        def is_valid_permit(v: str) -> bool:
            if not re.search(r"\d", v):
                return False
            if re.search(r"[a-z]", v):
                return False
            return True

        keyword_patterns = [
            r"([A-Z0-9][A-Z0-9/\-_.]+)\s*(?:PERMIT No\.|PERMIT|FILE No\.|File Number|Permission Number|Permission No\.?)",
            r"(?:Construction Permission Approved By|Construction Permission|Vide File No\.|File No\.|Permission Number|Permission No\.?|Permission|PERMIT No\.|PERMIT)\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-_.]+)",
        ]

        for pattern in keyword_patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
                groups = [group for group in match.groups() if group]
                if groups:
                    val = groups[0].strip()
                    if not is_date_or_stamp(val) and is_valid_permit(val):
                        return re.sub(r"\s+", " ", val).strip()

        for line in text.splitlines():
            if re.search(r"permission|file no|vide file no|permit no|permit|construction permission", line, flags=re.IGNORECASE):
                tokens = re.findall(r"[A-Z0-9][A-Z0-9/\-_.]+", line, flags=re.IGNORECASE)
                if tokens:
                    for token in reversed(tokens):
                        if ('/' in token or '-' in token) and len(token) > 5:
                            if not is_date_or_stamp(token) and is_valid_permit(token):
                                return re.sub(r"\s+", " ", token).strip()
                    last_token = tokens[-1]
                    if not is_date_or_stamp(last_token) and is_valid_permit(last_token):
                        return re.sub(r"\s+", " ", last_token).strip()

        fallback = re.search(r"\b[A-Z0-9]{2,}[/-][A-Z0-9/-]{2,}\b", text, flags=re.IGNORECASE)
        if fallback:
            val = fallback.group(0)
            if not is_date_or_stamp(val) and is_valid_permit(val):
                return re.sub(r"\s+", " ", val).strip()
        return None
