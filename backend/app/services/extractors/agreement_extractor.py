from __future__ import annotations
from typing import Any
from .base import BaseExtractor

class AgreementExtractor(BaseExtractor):
    def extract(self, text: str, page_results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {
            "applicant_name": self.extract_field_pipeline(text, "applicant_name", page_results),
            "owner_name": self.extract_field_pipeline(text, "owner_name", page_results),
            "property_address": self.extract_field_pipeline(text, "property_address", page_results),
            
            "document_number": self._look_for_label(text, [
                "Document Number", "DocumentNumber", "Doc No.", "Doc No", "DocNo", "Registration No.", "Reg No.", "RegNo."
            ], "document_number", page_results),
            
            "registration_details": self._look_for_label(text, [
                "Registration Details", "RegistrationDetails", "Registered At", "RegisteredAt", "registration details", "registered at"
            ], "registration_details", page_results),

            # Section 3: AOS Documents
            "aos_buyer_name": self.extract_field_pipeline(text, "aos_buyer_name", page_results),
            "aos_seller_name": self.extract_field_pipeline(text, "aos_seller_name", page_results),
            "aos_sale_deed_doc_number": self.extract_field_pipeline(text, "aos_sale_deed_doc_number", page_results),
            "aos_property_schedule": self.extract_field_pipeline(text, "aos_property_schedule", page_results),

            # Section 4: Ownership
            "purchaser_name": self.extract_field_pipeline(text, "purchaser_name", page_results),
            "purchaser_address": self.extract_field_pipeline(text, "purchaser_address", page_results),
            "purchaser_phone": self.extract_field_pipeline(text, "purchaser_phone", page_results),
            "ownership_type": self.extract_field_pipeline(text, "ownership_type", page_results),

            # Extras
            "agreement_value": self.extract_field_pipeline(text, "agreement_value", page_results),
            "project_name": self.extract_field_pipeline(text, "project_name", page_results),
            "registration_number": self.extract_field_pipeline(text, "registration_number", page_results),
            "registration_date": self.extract_field_pipeline(text, "registration_date", page_results)
        }
