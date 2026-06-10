from __future__ import annotations
from typing import Any
from .base import BaseExtractor

class AgreementExtractor(BaseExtractor):
    def extract(self, text: str, page_results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {
            "applicant_name": self._look_for_label(text, [
                "Name of Applicant", "Applicant Name", "ApplicantName", "Applicant", "Sri/Smt.", "Mrs.", "Mr."
            ], "applicant_name", page_results),
            
            "property_address": self._look_for_label(text, [
                "Property Address", "PropertyAddress", "Address", "Site Address", "R/o.", "R/o", "Resident of"
            ], "property_address", page_results),
            
            "document_number": self._look_for_label(text, [
                "Document Number", "DocumentNumber", "Doc No.", "Doc No", "DocNo", "Registration No.", "Reg No.", "RegNo."
            ], "document_number", page_results),
            
            "registration_details": self._look_for_label(text, [
                "Registration Details", "RegistrationDetails", "Registered At", "RegisteredAt", "registration details", "registered at"
            ], "registration_details", page_results)
        }
