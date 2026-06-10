from __future__ import annotations
import re
from typing import Any
from .base import BaseExtractor

class ScheduleExtractor(BaseExtractor):
    def extract(self, text: str, page_results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        survey = self._look_for_label(text, [
            "Survey Number", "Survey No.", "Survey No", "SurveyNo", "Sy No.", "Sy No", "SyNo", "SURVEY NO", "Survey No./Gramkhantam/Abadi"
        ], "survey_number", page_results)
        
        # Fallback if survey is not found
        if not survey.get("value"):
            fallback_val = self._extract_survey_fallback(text)
            if fallback_val:
                page_num = self._find_source_page_for_line(fallback_val, page_results)
                ocr_conf = self._get_ocr_confidence(fallback_val, page_num, page_results)
                survey = {
                    "value": fallback_val,
                    "source_page": page_num + 1,
                    "ocr_confidence": float(ocr_conf),
                    "regex_confidence": 0.60,
                    "final_confidence": float((0.7 * ocr_conf) + (0.3 * 0.60))
                }

        return {
            "survey_number": survey,
            
            "plot_number": self._look_for_label(text, [
                "Plot Number", "Plot No.", "Plot No", "PlotNo.", "PlotNo"
            ], "plot_number", page_results),
            
            "built_up_area": self._look_for_label(text, [
                "Built-up Area", "Built Up Area", "Builtup Area", "Built-upArea", "BuiltUpArea", "built-up area as per sanctioned plan"
            ], "built_up_area", page_results, is_area_field=True),
            
            "land_area": self._look_for_label(text, [
                "Land Area", "LandArea", "Extent of Land", "Plot Area", "PlotArea"
            ], "land_area", page_results, is_area_field=True)
        }

    def _extract_survey_fallback(self, text: str) -> str | None:
        net_plot_match = re.search(r"Net Plot Area[^\n]+?(\d+/[A-Z0-9/,-]+(?:\s*,\s*\d+/[A-Z0-9/,-]+)*)", text, flags=re.IGNORECASE)
        if net_plot_match:
            return re.sub(r"\s+", " ", net_plot_match.group(1)).strip()
        
        # Simple checker to reject standard dates inside the fallback
        MONTH_ABBRS = {"jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"}
        
        matches = re.findall(r"\b\d{2,4}/[A-Z0-9/,-]+\b", text, flags=re.IGNORECASE)
        if matches:
            for m in matches:
                # Reject if matches a date
                m_clean = m.strip().lower()
                if re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", m_clean):
                    continue
                if re.search(r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b", m_clean):
                    continue
                is_abbr = False
                for abbr in MONTH_ABBRS:
                    if m_clean.startswith(abbr):
                        is_abbr = True
                        break
                if not is_abbr:
                    return re.sub(r"\s+", " ", m).strip()
        return None
