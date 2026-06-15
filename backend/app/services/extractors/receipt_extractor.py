from __future__ import annotations
from typing import Any
from .base import BaseExtractor

class ReceiptExtractor(BaseExtractor):
    def extract(self, text: str, page_results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {
            "rera_registration_number": self.extract_field_pipeline(text, "rera_registration_number", page_results)
        }
