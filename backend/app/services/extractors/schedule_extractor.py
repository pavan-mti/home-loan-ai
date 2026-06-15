from __future__ import annotations
from typing import Any
from .base import BaseExtractor

class ScheduleExtractor(BaseExtractor):
    def extract(self, text: str, page_results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {
            # Section 9 - Location
            "survey_number": self.extract_field_pipeline(text, "survey_number", page_results),
            "plot_number": self._look_for_label(text, [
                "Plot Number", "Plot No.", "Plot No", "PlotNo.", "PlotNo"
            ], "plot_number", page_results),
            "door_number": self.extract_field_pipeline(text, "door_number", page_results),
            "village": self.extract_field_pipeline(text, "village", page_results),
            "mandal": self.extract_field_pipeline(text, "mandal", page_results),
            "district": self.extract_field_pipeline(text, "district", page_results),
            "ts_number": self.extract_field_pipeline(text, "ts_number", page_results),
            "ward": self.extract_field_pipeline(text, "ward", page_results),
            "taluka": self.extract_field_pipeline(text, "taluka", page_results),
            "layout_approval_date": self.extract_field_pipeline(text, "layout_approval_date", page_results),
            "layout_approval_validity": self.extract_field_pipeline(text, "layout_approval_validity", page_results),
            "approved_plan_authority": self.extract_field_pipeline(text, "approved_plan_authority", page_results),

            # Section 8 - Financial
            "market_value": self._look_for_label(text, [
                "Market Value", "MarketValue", "Fair Market Value", "Value of Property"
            ], "market_value", page_results),
            "guideline_value": self._look_for_label(text, [
                "Guideline Value", "GuidelineValue", "Govt Value", "Government Value"
            ], "guideline_value", page_results),
            "mortgage_details": self.extract_field_pipeline(text, "mortgage_details", page_results),
            "ftl_buffer_zone_details": self.extract_field_pipeline(text, "ftl_buffer_zone_details", page_results),

            # Section 7 - Legal
            "legal_disputes": self._look_for_label(text, [
                "Legal Disputes", "Disputes", "Litigations", "Court Cases"
            ], "legal_disputes", page_results),
            "is_disputed": self._look_for_label(text, [
                "Is Disputed", "Disputed Status"
            ], "is_disputed", page_results),
            "legal_opinion": self.extract_field_pipeline(text, "legal_opinion", page_results),

            # Section 5 - Property Description
            "built_up_area": self.extract_field_pipeline(text, "built_up_area", page_results),
            "land_area": self.extract_field_pipeline(text, "land_area", page_results),
            "built_up_area_sqft": self.extract_field_pipeline(text, "built_up_area_sqft", page_results),
            "land_area_sqyd": self.extract_field_pipeline(text, "land_area_sqyd", page_results),
            "property_description": self.extract_field_pipeline(text, "property_description", page_results),
            "property_tenure": self.extract_field_pipeline(text, "property_tenure", page_results),

            # Section 1 - General
            "valuation_purpose": self.extract_field_pipeline(text, "valuation_purpose", page_results),
            "inspection_date": self.extract_field_pipeline(text, "inspection_date", page_results),
            "valuation_date": self.extract_field_pipeline(text, "valuation_date", page_results),

            # Section 6 - Prohibited
            "prohibited_property_details": self.extract_field_pipeline(text, "prohibited_property_details", page_results),

            # Section 13 - Municipality
            "municipality_type": self.extract_field_pipeline(text, "municipality_type", page_results),

            # Section 14 - Govt Enactments
            "under_govt_enactment": self.extract_field_pipeline(text, "under_govt_enactment", page_results),
            "enactment_details": self.extract_field_pipeline(text, "enactment_details", page_results),

            # Extras
            "state": self.extract_field_pipeline(text, "state", page_results),
            "pincode": self.extract_field_pipeline(text, "pincode", page_results)
        }
