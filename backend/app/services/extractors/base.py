from __future__ import annotations
import re
from typing import Any

class BaseExtractor:
    def extract(self, text: str, page_results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        raise NotImplementedError("Each extractor must implement extract()")

    def _find_source_page_for_line(self, val: str, page_results: list[dict[str, Any]]) -> int:
        for i, page in enumerate(page_results):
            for line in page.get("lines", []):
                line_text = line.get("text", "").strip()
                if line_text and (val in line_text or line_text in val):
                    return i
        return 0

    def _get_ocr_confidence(self, val: str, page_num: int, page_results: list[dict[str, Any]]) -> float:
        if page_num < len(page_results):
            page = page_results[page_num]
            for line in page.get("lines", []):
                line_text = line.get("text", "").strip()
                if line_text and (val in line_text or line_text in val):
                    return float(line.get("confidence", 1.0))
            return float(page.get("confidence", 1.0))
        return 1.0

    def _look_for_label(
        self,
        text: str,
        labels: list[str],
        field_key: str,
        page_results: list[dict[str, Any]],
        is_area_field: bool = False
    ) -> dict[str, Any]:
        from app.services.documents import clean_and_merge_ocr_lines
        clean_text = text.replace("|", " ")
        merged_text = clean_and_merge_ocr_lines(clean_text)
        lines = merged_text.splitlines()
        for label in labels:
            pattern = rf"(?<!\w){re.escape(label)}(?!\w)\s*[:\-–—=]?\s*([^\n]*)"
            for i, line in enumerate(lines):
                match = re.search(pattern, line, flags=re.IGNORECASE)
                if match:
                    val = match.group(1).strip()
                    val = val.strip(" |").strip()
                    val_index = i
                    
                    # End-of-line fallback
                    if not val or not re.search(r"[a-zA-Z0-9]", val):
                        if i + 1 < len(lines):
                            val = lines[i + 1].strip()
                            val = val.strip(" |").strip()
                            val_index = i + 1
                            if not val or any(re.search(rf"(?<!\w){re.escape(lbl)}(?!\w)", val, flags=re.IGNORECASE) for lbl in [
                                "Name of Applicant", "Applicant Name", "Survey", "Plot", "HouseNo", "Street"
                            ]):
                                continue
                                
                    val_lower = val.lower()
                    
                    # Common Filters
                    if any(x in val_lower for x in ["gramkhantam", "abadi", "houseno", "door no", "plotno", "street / road", "locality name"]):
                        continue
                    if any(word in val_lower.split() for word in ["shall", "should", "will", "would", "must", "unless", "until", "register", "registering", "produced", "hereby"]):
                        continue
                    if is_area_field or any(term in label.lower() or term in field_key for term in ["area", "built-up", "land"]):
                        if any(x in val_lower for x in ["fee", "fees", "charge", "charges", "deposit", "policy", "permit", "payment", "total"]):
                            continue
                        if not re.search(r"\d", val):
                            continue
                    limit = 250 if field_key == "property_address" else 150
                    if len(val) > limit:
                        continue
                    if not re.search(r"[a-zA-Z0-9]", val):
                        continue
                        
                    # Continuations & Lookaheads
                    page_num = self._find_source_page_for_line(val, page_results)
                    
                    # Heuristic 1: Address continuation lookahead
                    if field_key == "property_address":
                        current_address = val
                        for j in range(val_index + 1, min(len(lines), val_index + 8)):
                            next_line = lines[j].strip()
                            if not next_line:
                                continue
                            if any(re.search(rf"(?<!\w){re.escape(lbl)}(?!\w)", next_line, flags=re.IGNORECASE) for lbl in [
                                "Name of Applicant", "Applicant Name", "Applicant", "Survey Number", "Survey No", "Plot Number",
                                "Plot No", "Plot Area", "Land Area", "Net Plot Area", "Document Number", "Registration Details"
                            ]):
                                break

                            has_pincode = re.search(r"\b\d{6}\b|\b5[oO\d]{5}\b", next_line)
                            is_address_indicator = any(kw in next_line.lower() for kw in [
                                "road", "street", "lane", "nagar", "colony", "goshala", "village", "mandal",
                                "district", "dist", "state", "telangana", "pincode", "pin:", "h.no", "plot",
                                "flat", "phase", "sector", "puppalaguda", "narsingi", "kokapet", "ramachandrapuram",
                                "sangareddy", "medak", "hills", "pws", "h no", "d no", "d.no", "door", "floor"
                            ]) or next_line.endswith(",") or next_line.endswith("-")
                            
                            if is_address_indicator or has_pincode:
                                current_address = current_address + " " + next_line
                                if has_pincode:
                                    break
                            else:
                                break
                        val = re.sub(r"\s+", " ", current_address).strip()

                    # Heuristic 2: Applicant Name continuation lookahead
                    elif field_key == "applicant_name":
                        current_name = val
                        if any(x in current_name.lower() for x in ["w/o", "s/o", "d/o", "c/o", "late", "sri"]):
                            for j in range(val_index + 1, min(len(lines), val_index + 3)):
                                next_line = lines[j].strip()
                                if not next_line:
                                    continue
                                if any(re.search(rf"(?<!\w){re.escape(lbl)}(?!\w)", next_line, flags=re.IGNORECASE) for lbl in [
                                    "Name of Applicant", "Applicant Name", "Survey", "Plot", "HouseNo", "Street",
                                    "Represented By", "Developer", "Builder", "LTP", "Architect"
                                ]):
                                    break
                                
                                next_line_clean = re.sub(r"\(.*?\)", "", next_line).strip()
                                if next_line_clean:
                                    current_name = current_name + " " + next_line_clean
                                    break
                        val = re.sub(r"\s+", " ", current_name).strip()

                    ocr_conf = self._get_ocr_confidence(val, page_num, page_results)
                    regex_conf = 1.0 if label.lower() in val.lower() else 0.85
                    if len(label) < 4:
                        regex_conf = 0.70
                    
                    final_conf = (0.7 * ocr_conf) + (0.3 * regex_conf)
                    
                    return {
                        "value": val,
                        "source_page": page_num + 1,
                        "ocr_confidence": float(ocr_conf),
                        "regex_confidence": float(regex_conf),
                        "final_confidence": float(final_conf)
                    }
        return {
            "value": None,
            "source_page": None,
            "ocr_confidence": 0.0,
            "regex_confidence": 0.0,
            "final_confidence": 0.0
        }
