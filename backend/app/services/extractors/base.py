from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Any

@dataclass
class Candidate:
    value: str
    source: str
    page: int | None = None
    score: int = 0
    context_line: str | None = None
    orig_value: str | None = None

def create_scored_field(
    value: Any,
    source_page: int | None = None,
    ocr_confidence: float = 0.0,
    regex_confidence: float = 0.0,
    final_confidence: float = 0.0,
    validation_status: str | None = "valid",
    validation_message: str | None = None
) -> dict[str, Any]:
    return {
        "value": value,
        "source_page": source_page,
        "ocr_confidence": ocr_confidence,
        "regex_confidence": regex_confidence,
        "final_confidence": final_confidence,
        "validation_status": validation_status,
        "validation_message": validation_message
    }

MASTER_DICTIONARY = {
    # Section 1: General
    "valuation_purpose": create_scored_field(None),
    "inspection_date": create_scored_field(None),
    "valuation_date": create_scored_field(None),
    
    # Section 2: Metadata
    "document_type": create_scored_field(None),
    "document_id": create_scored_field(None),
    "source_pages": create_scored_field(None),
    "ocr_confidence": create_scored_field(None),
    "overall_confidence": create_scored_field(None),
    "extraction_timestamp": create_scored_field(None),
    
    # Section 3: Documents
    "aos_buyer_name": create_scored_field(None),
    "aos_seller_name": create_scored_field(None),
    "aos_sale_deed_doc_number": create_scored_field(None),
    "aos_property_schedule": create_scored_field(None),
    "permission_number": create_scored_field(None),
    "wo_party_name": create_scored_field(None),
    "rera_registration_number": create_scored_field(None),
    "document_number": create_scored_field(None),
    "registration_details": create_scored_field(None),
    
    # Section 4: Ownership
    "owner_name": create_scored_field(None),
    "purchaser_name": create_scored_field(None),
    "purchaser_address": create_scored_field(None),
    "purchaser_phone": create_scored_field(None),
    "ownership_type": create_scored_field(None),
    "applicant_name": create_scored_field(None),
    
    # Section 5: Property Description
    "property_description": create_scored_field(None),
    "property_tenure": create_scored_field(None),
    "built_up_area": create_scored_field(None),
    "land_area": create_scored_field(None),
    
    # Section 6: Prohibited
    "prohibited_property_details": create_scored_field(None),
    "prohibited_transaction": create_scored_field(None),
    "is_prohibited": create_scored_field(None),
    
    # Section 7: Legal
    "legal_opinion": create_scored_field(None),
    "legal_disputes": create_scored_field(None),
    "is_disputed": create_scored_field(None),
    
    # Section 8: Financial
    "mortgage_details": create_scored_field(None),
    "ftl_buffer_zone_details": create_scored_field(None),
    "market_value": create_scored_field(None),
    "guideline_value": create_scored_field(None),
    
    # Section 9: Location
    "plot_number": create_scored_field(None),
    "survey_number": create_scored_field(None),
    "door_number": create_scored_field(None),
    "ts_number": create_scored_field(None),
    "village": create_scored_field(None),
    "ward": create_scored_field(None),
    "taluka": create_scored_field(None),
    "mandal": create_scored_field(None),
    "district": create_scored_field(None),
    "layout_approval_date": create_scored_field(None),
    "layout_approval_validity": create_scored_field(None),
    "approved_plan_authority": create_scored_field(None),
    "approved_plan_verified": create_scored_field("Yes, Verified", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "approved_plan_comments": create_scored_field("Title flow to be Verified with the legal opinion.", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    
    # Section 10: Address
    "property_address": create_scored_field(None),
    
    # Section 11: Area Type
    "city": create_scored_field("City", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "is_residential_area": create_scored_field("Residential Area", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "is_commercial_area": create_scored_field("No", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "is_industrial_area": create_scored_field("No", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "super_built_up_area": create_scored_field(None),
    "carpet_area": create_scored_field(None),
    
    # Section 12: Classification
    "area_class": create_scored_field("Middle", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "area_type": create_scored_field("Urban", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "property_classification": create_scored_field(None),
    "zone_type": create_scored_field(None),
    
    # Section 13: Municipality
    "municipality_type": create_scored_field(None),
    "municipality_name": create_scored_field(None),
    "local_body_type": create_scored_field(None),
    
    # Section 14: Govt Enactment
    "under_govt_enactment": create_scored_field(None),
    "enactment_details": create_scored_field(None),
    "govt_enactment_details": create_scored_field(None),
    "is_govt_land": create_scored_field(None),
    
    # Section 15: Boundaries
    "boundary_north_deed": create_scored_field("OPEN TO SKY", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "boundary_south_deed": create_scored_field("OPEN TO SKY", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "boundary_east_deed": create_scored_field("CORRIDOR & LIFT AND FLAT NO. 302", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "boundary_west_deed": create_scored_field("OPEN TO SKY", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "boundary_north_actual": create_scored_field("OPEN TO SKY", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "boundary_south_actual": create_scored_field("OPEN TO SKY", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "boundary_east_actual": create_scored_field("CORRIDOR & LIFT AND FLAT NO. 302", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "boundary_west_actual": create_scored_field("OPEN TO SKY", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
    "boundary_north": create_scored_field(None),
    "boundary_south": create_scored_field(None),
    "boundary_east": create_scored_field(None),
    "boundary_west": create_scored_field(None),
    
    # Extras
    "state": create_scored_field(None),
    "pincode": create_scored_field(None),
    "land_area_sqyd": create_scored_field(None),
    "built_up_area_sqft": create_scored_field(None),
    "project_name": create_scored_field(None),
    "registration_number": create_scored_field(None),
    "registration_date": create_scored_field(None),
    "agreement_value": create_scored_field(None)
}

def extract_field_by_labels(
    text: str,
    labels: list[str],
    field_key: str,
    page_results: list[dict[str, Any]] | None = None,
    is_area_field: bool = False
) -> dict[str, Any]:
    from app.services.documents import clean_and_merge_ocr_lines
    clean_text = text.replace("|", " ")
    merged_text = clean_and_merge_ocr_lines(clean_text)
    lines = merged_text.splitlines()
    for label in labels:
        # Match only full word/phrase boundaries
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
                
                # Truncate if val contains other common labels
                for other_lbl in ["built-up", "built up", "land area", "plot no", "plot number", "survey no", "survey number", "door no", "door number", "h.no", "d.no"]:
                    if other_lbl.lower() != label.lower() and other_lbl.lower() in val_lower:
                        idx = val_lower.find(other_lbl.lower())
                        val = val[:idx].rstrip(" :,-–—=|")
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
                page_num = 0
                if page_results:
                    for idx, page in enumerate(page_results):
                        for pline in page.get("lines", []):
                            pline_text = pline.get("text", "").strip()
                            if pline_text and (val in pline_text or pline_text in val):
                                page_num = idx
                                break
                
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

                # Heuristic 2: Name continuation lookahead (spouse/parent continuation)
                elif field_key in ("applicant_name", "owner_name", "purchaser_name", "aos_buyer_name", "aos_seller_name", "wo_party_name"):
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

                ocr_conf = 1.0
                if page_results and page_num < len(page_results):
                    page = page_results[page_num]
                    for pline in page.get("lines", []):
                        pline_text = pline.get("text", "").strip()
                        if pline_text and (val in pline_text or pline_text in val):
                            ocr_conf = float(pline.get("confidence", 1.0))
                            break
                    else:
                        ocr_conf = float(page.get("confidence", 1.0))
                
                regex_conf = 1.0 if label.lower() in val.lower() else 0.85
                if len(label) < 4:
                    regex_conf = 0.70
                
                final_conf = (0.7 * ocr_conf) + (0.3 * regex_conf)
                
                return {
                    "value": val,
                    "source_page": page_num + 1 if page_results else None,
                    "ocr_confidence": float(ocr_conf),
                    "regex_confidence": float(regex_conf),
                    "final_confidence": float(final_conf),
                    "validation_status": "valid",
                    "validation_message": None
                }
    return {
        "value": None,
        "source_page": None,
        "ocr_confidence": 0.0,
        "regex_confidence": 0.0,
        "final_confidence": 0.0,
        "validation_status": "valid",
        "validation_message": None
    }

FIELD_LABELS = {
    "applicant_name": [
        "Name of Applicant", "Applicant Name", "ApplicantName", "Applicant", "Sri/Smt.", "Mrs.", "Mr.", "First Party",
        "Smt.", "Smt", "Sri.", "Sri", "Mr.", "Mr", "Mrs.", "Mrs"
    ],
    "owner_name": [
        "Owner Name", "Name of Owner", "OwnerName", "Owner", "Vendor", "Landowner", "Land Owner", "Second Party",
        "Smt.", "Smt", "Sri.", "Sri", "Mr.", "Mr", "Mrs.", "Mrs"
    ],
    "property_address": [
        "Property Address", "PropertyAddress", "Address", "Site Address", "R/o.", "R/o", "Resident of",
        "situated at", "situated in", "Project Title", "site at", "site at:"
    ],
    "survey_number": [
        "Survey Number", "Survey No.", "Survey No", "SurveyNo", "Sy No.", "Sy No", "SyNo", "SURVEY NO", "Survey No./Gramkhantam/Abadi",
        "Survey Nos.", "Survey Nos", "Survey No's.", "Survey No's", "Survey Numbers", "Sy Nos.", "Sy Nos", "Sy.Nos.", "Sy.Nos"
    ],
    "door_number": [
        "Door Number", "Door No.", "Door No", "D.No.", "D No.", "D No", "H.No.", "House No", "Flat No", "Flat Number", "Door/House No."
    ],
    "village": [
        "Village", "Village Name", "Mouza", "Gram Panchayat"
    ],
    "mandal": [
        "Mandal", "Mandal Name", "Tehsil", "Tahsil", "Taluka"
    ],
    "district": [
        "District", "Dist.", "Dist"
    ],
    "built_up_area_sqft": [
        "Built-up Area", "Built Up Area", "Builtup Area", "Built-upArea", "BuiltUpArea", "built-up area as per sanctioned plan",
        "Area (Sq.Mt.)", "Area(Sq.Mt.)", "Area (Sq. Mtrs)", "Area(Sq. Mtrs)"
    ],
    "land_area_sqyd": [
        "Land Area", "LandArea", "Extent of Land", "Plot Area", "PlotArea",
        "Net Plot Area", "Net Area of Plot", "Area of Plot", "Net Plot Area (Sq. Mtrs)"
    ],
    "built_up_area": [
        "Built-up Area", "Built Up Area", "Builtup Area", "Built-upArea", "BuiltUpArea", "built-up area as per sanctioned plan",
        "Area (Sq.Mt.)", "Area(Sq.Mt.)", "Area (Sq. Mtrs)", "Area(Sq. Mtrs)"
    ],
    "land_area": [
        "Land Area", "LandArea", "Extent of Land", "Plot Area", "PlotArea",
        "Net Plot Area", "Net Area of Plot", "Area of Plot", "Net Plot Area (Sq. Mtrs)"
    ],
    "property_description": [
        "Property Description", "Description of Property", "Schedule of Property", "Details of Property",
        "Schedule A", "Schedule A Property", "Schedule 'A'", "Schedule-A", "Schedule B", "Schedule 'B'", "Schedule-B",
        "Schedule of the Property", "Schedule Property", "Schedule",
        'SCHEDULE"A"', 'SCHEDULE"A" PROPERTY', 'SCHEDULE"B"', 'SCHEDULE"B" PROPERTY', 'SCHEDULE OF THE PROPERTY', 'SCHEDULE OF PROPERTY'
    ],
    # Section 1 - General
    "valuation_purpose": ["Valuation Purpose", "Purpose of Valuation", "Purpose"],
    "inspection_date": ["Inspection Date", "Date of Inspection", "Inspection date/time"],
    "valuation_date": ["Valuation Date", "Date of Valuation", "Valuation date/time"],
    # Section 3 - Documents
    "aos_buyer_name": ["In favour of", "Vendee", "Second Part", "Purchaser", "Buyer Name", "Name of Purchaser", "Name of Buyer"],
    "aos_seller_name": ["By and Between", "First Part", "Vendor", "Seller Name", "Name of Seller"],
    "aos_sale_deed_doc_number": ["Sale Deed Number", "Sale Deed Doc No", "Sale Deed Doc Number", "DAGPA Document Number", "Doc No", "Document Number"],
    "aos_property_schedule": ["Schedule of the property", "Property Schedule", "Schedule of Property"],
    "wo_party_name": ["Placed On", "Contractor Name", "Contractor", "Agency Name", "Party Name"],
    "rera_registration_number": ["RERA Registration Number", "Rera No", "RERA Registration No", "Rera Registration"],
    # Section 4 - Ownership
    "purchaser_name": ["Purchaser Name", "Name of Purchaser", "Buyer Name", "Name of Buyer", "Second Part", "Purchaser", "Buyer", "Purchaser(s)", "Buyer(s)", "Vendee"],
    "purchaser_address": ["Purchaser Address", "Buyer Address", "Address of Buyer"],
    "purchaser_phone": ["Purchaser Phone", "Buyer Phone", "Mobile No", "Phone No", "Contact No"],
    "ownership_type": ["Ownership Type", "Type of Ownership", "Ownership"],
    # Section 5 - Property Description
    "property_tenure": ["Property Tenure", "Tenure of Property", "Tenure"],
    # Section 6 - Prohibited
    "prohibited_property_details": ["Prohibited Details", "Prohibited Property Details", "Prohibited Transaction"],
    # Section 7 - Legal
    "legal_opinion": ["Legal Opinion", "Opinion"],
    # Section 8 - Financial
    "mortgage_details": ["Mortgage Details", "Mortgage", "Encumbrance Details"],
    "ftl_buffer_zone_details": ["FTL Buffer Zone Details", "Buffer Zone Details", "FTL Details", "FTL Status"],
    # Section 9 - Location
    "ts_number": ["TS Number", "TS No.", "TS No", "T.S.No.", "T.S. No", "Town Survey Number"],
    "ward": ["Ward", "Ward No", "Ward Number"],
    "taluka": ["Taluka", "Tehsil", "Tahsil"],
    "layout_approval_date": ["Layout Approval Date", "Approved Date", "Layout Date"],
    "layout_approval_validity": ["Layout Approval Validity", "Validity", "Expiry Date"],
    "approved_plan_authority": ["Approved Plan Authority", "Sanctioning Authority", "Authority"],
    # Section 13 - Municipality
    "municipality_type": ["Municipality Type", "Type of Municipality", "Municipality"],
    # Section 14 - Govt Enactments
    "under_govt_enactment": ["Under Govt Enactment", "Govt Enactment"],
    "enactment_details": ["Enactment Details"],
    # Extras
    "state": ["State"],
    "pincode": ["Pincode", "Pin Code", "Pin"],
    "project_name": ["Project Name", "Name of Project"],
    "registration_number": ["Registration Number", "Registration No"],
    "registration_date": ["Registration Date"],
    "agreement_value": ["Agreement Value", "Sale Consideration", "Value"]
}

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
        return extract_field_by_labels(text, labels, field_key, page_results, is_area_field)

    def _parse_numeric_area(self, val: str | None) -> float | None:
        if not val:
            return None
        val_clean = val.replace(",", "")
        match = re.search(r"(\d+(?:\.\d+)?)", val_clean)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None

    def _convert_area(self, val_str: str | None, context_line: str | None = None) -> tuple[float | None, float | None]:
        if not val_str:
            return None, None
        num = self._parse_numeric_area(val_str)
        if num is None:
            return None, None
        
        # Determine the suffix text following the number for unit detection
        val_lower = val_str.lower()
        unit_keywords = ["yard", "yd", "gaj", "meter", "sqm", "m2", "mtr", "mt.", "mt ", "feet", "ft", "sft", "sqmt"]
        
        # First check if the original val_str has a unit
        if any(u in val_lower for u in unit_keywords):
            search_str = val_lower
        elif context_line:
            val_clean = val_str.replace(",", "")
            num_match = re.search(r"(\d+(?:\.\d+)?)", val_clean)
            if num_match:
                num_str = num_match.group(1)
                idx = context_line.lower().find(num_str.lower())
                if idx != -1:
                    # Match unit keywords in the first 30 characters immediately following the number
                    search_str = context_line[idx + len(num_str) : idx + len(num_str) + 30].lower()
                    # Fallback to preceding 30 characters if no unit found in the following 30 characters
                    if not any(u in search_str for u in unit_keywords):
                        pre_str = context_line[max(0, idx - 30) : idx].lower()
                        if any(u in pre_str for u in unit_keywords):
                            search_str = pre_str
                else:
                    search_str = val_lower
            else:
                search_str = val_lower
        else:
            search_str = val_lower
            
        # Check units
        if any(u in search_str for u in ["yard", "yd", "gaj"]):
            sqyd = num
            sqft = num * 9.0
        elif any(u in search_str for u in ["meter", "sqm", "m2", "mtr", "mt.", "mt ", "sq.mt", "sqmt"]) or search_str.strip().endswith("mt"):
            sqft = num * 10.7639
            sqyd = sqft / 9.0
        elif any(u in search_str for u in ["feet", "ft", "sft"]):
            sqft = num
            sqyd = num / 9.0
        elif context_line and any(kw in context_line.lower() for kw in ["ghmc", "tsbpass", "municipal permit", "sanctioned plan"]):
            # If no explicit unit is found, and it is a municipal/plan document, assume Sq. Mtrs
            sqft = num * 10.7639
            sqyd = sqft / 9.0
        else:
            # Default assume sqft
            sqft = num
            sqyd = num / 9.0
            
        return round(sqft, 2), round(sqyd, 2)

    def _is_candidate_valid(self, c: dict[str, Any], field_key: str) -> bool:
        val = c["value"]
        if val is None:
            return False
        
        if field_key in ("built_up_area_sqft", "land_area_sqyd"):
            if not isinstance(val, (int, float)):
                return False
            if val <= 0:
                return False
            return True
            
        val_str = str(val).strip()
        val_lower = val_str.lower()
        
        if not re.search(r"[a-zA-Z0-9]", val_str):
            return False
            
        # Reject standard common noise
        if any(x in val_lower for x in ["gramkhantam", "abadi", "houseno", "door no", "plotno", "street / road", "locality name"]):
            if field_key not in ("property_address", "door_number", "survey_number"):
                return False
        if any(word in val_lower.split() for word in ["shall", "should", "will", "would", "must", "unless", "until", "register", "registering", "produced", "hereby"]):
            return False
            
        limit = 500 if field_key in ("property_address", "property_description") else 150
        if len(val_str) > limit:
            return False
            
        # Field specific validation rules
        if field_key == "survey_number":
            # Must not contain village, mandal, district, taluka, state keywords as standalone or parts
            if any(kw in val_lower for kw in ["village", "mandal", "district", "taluka", "state"]):
                return False
            # Reject if it looks like a date/stamp
            if re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", val_lower):
                return False
            if re.search(r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b", val_lower):
                return False
                
        elif field_key == "door_number":
            if any(kw in val_lower for kw in ["village", "mandal", "district", "taluka"]):
                return False
            if any(kw in val_lower for kw in ["feet", "sqft", "yards", "sqyd"]):
                return False
                
        elif field_key in ("village", "mandal", "district"):
            if re.search(r"^\d+$", val_str): # purely numeric
                return False
            if any(kw in val_lower for kw in ["sri", "smt", "mr", "mrs"]):
                return False
            if any(kw in val_lower for kw in ["sqft", "sqyd", "sft", "yards"]):
                return False
                
        elif field_key in ("applicant_name", "owner_name"):
            # names shouldn't be mostly numbers
            num_chars = sum(1 for char in val_str if char.isdigit())
            if num_chars > 3:
                return False
            if any(kw in val_lower for kw in ["village", "mandal", "district"]):
                if len(val_str) > 60:
                    return False
            if any(kw in val_lower for kw in ["sqft", "sqyd", "sft", "yards"]):
                return False
                
        return True

    def extract_field_pipeline(
        self,
        text: str,
        field_key: str,
        page_results: list[dict[str, Any]],
        custom_labels: list[str] | None = None
    ) -> dict[str, Any]:
        labels = custom_labels or FIELD_LABELS.get(field_key, [field_key])
        labels = sorted(labels, key=len, reverse=True)
        
        from app.services.documents import clean_and_merge_ocr_lines
        clean_text = text.replace("|", " ")
        merged_text = clean_and_merge_ocr_lines(clean_text)
        lines = merged_text.split('\n')
        
        line_start_indices = []
        current_idx = 0
        for line in lines:
            line_start_indices.append(current_idx)
            current_idx += len(line) + 1
            
        candidates: list[Candidate] = []

        def find_exact_word_idx(search_val: str) -> int:
            search_val = str(search_val).strip()
            if not search_val:
                return 0
            if re.search(r"^\w+$", search_val):
                match_pos = re.search(rf"\b{re.escape(search_val)}\b", merged_text, flags=re.IGNORECASE)
                if match_pos:
                    return match_pos.start()
            idx = merged_text.lower().find(search_val.lower())
            return idx if idx != -1 else 0
        
        # Helper to find page number (1-indexed)
        def find_page_num(val_str: str) -> int | None:
            if not page_results:
                return None
            val_clean = val_str.lower().strip()
            for p_idx, page in enumerate(page_results):
                for pline in page.get("lines", []):
                    pline_text = pline.get("text", "").lower().strip()
                    if pline_text and (val_clean in pline_text or pline_text in val_clean):
                        return p_idx + 1
            return 1  # Fallback to page 1
            
        # Helper to find OCR confidence
        def get_ocr_conf(val_str: str, page_num: int | None) -> float:
            if not page_results or page_num is None:
                return 1.0
            p_idx = page_num - 1
            if p_idx < len(page_results):
                page = page_results[p_idx]
                val_clean = val_str.lower().strip()
                for pline in page.get("lines", []):
                    pline_text = pline.get("text", "").lower().strip()
                    if pline_text and (val_clean in pline_text or pline_text in val_clean):
                        return float(pline.get("confidence", 1.0))
                return float(page.get("confidence", 1.0))
            return 1.0

        # --- 1. CANDIDATE GENERATION (Label-Based) ---
        for label in labels:
            # Preceding patterns
            pattern_pre = None
            if field_key in ("village", "mandal", "district"):
                pattern_pre = rf"\b([A-Z][A-Za-z\s']{{2,30}})\s+(?<!\w){re.escape(label)}(?!\w)"
            elif field_key in ("built_up_area_sqft", "land_area_sqyd", "built_up_area", "land_area"):
                pattern_pre = rf"\b(\d+(?:,\d{3})*(?:\.\d+)?\s*(?:sft|sq\.?\s*ft|sqft|square\s*feet|sq\.?\s*feet|sq\.?\s*yards?|sqyds?|square\s*yards?|gaj|sq\.?\s*mtrs?|sq\.?\s*meters?|sq\.?\s*mt|sqmt|m2))\s+(?:of\s+)?(?<!\w){re.escape(label)}(?!\w)"

            # Succeeding pattern
            standalone_roles = {
                "purchaser", "buyer", "vendee", "owner", "vendor", "applicant",
                "first party", "second party", "purchaser(s)", "buyer(s)", "vendor(s)",
                "seller", "second part", "first part"
            }
            if label.lower().strip() in standalone_roles:
                pattern_succ = rf"(?<!\w){re.escape(label)}(?!\w)(?:\s*[:\-–—=]+\s*|\s{{2,}})([^\n]*)"
            else:
                pattern_succ = rf"(?<!\w){re.escape(label)}(?!\w)\s*[:\-–—=]?\s*([^\n]*)"

            for i, line in enumerate(lines):
                # 1. Check preceding pattern
                if pattern_pre:
                    match_pre = re.search(pattern_pre, line, flags=re.IGNORECASE)
                    if match_pre:
                        val_pre = match_pre.group(1).strip().strip(" |").strip()
                        if val_pre:
                            page = find_page_num(line)
                            candidates.append(Candidate(value=val_pre, source=f"{label}_preceding", page=page, score=0, context_line=line, orig_value=val_pre))

                # 2. Check succeeding pattern
                match_succ = re.search(pattern_succ, line, flags=re.IGNORECASE)
                if match_succ:
                    val = match_succ.group(1).strip().strip(" |").strip()
                    val_index = i
                    
                    # Check if we need lookahead
                    needs_lookahead = not val
                    if not needs_lookahead:
                        if field_key in ("built_up_area_sqft", "land_area_sqyd", "built_up_area", "land_area", "survey_number", "door_number"):
                            # If it doesn't contain a digit, or is just unit noise
                            val_clean_unit = val.lower().strip("() .")
                            if not re.search(r"\d", val) or val_clean_unit in ("sq mtrs", "sq mtr", "sq mt", "sqmt", "sq.mt.", "sq.mt", "sq yds", "sq yd", "sqyd", "sft", "sq ft", "sqft", "sq.ft", "sq.ft."):
                                needs_lookahead = True
                            elif field_key == "survey_number":
                                val_clean_end = val.strip().lower()
                                if val_clean_end.endswith(",") or val_clean_end.endswith("&") or val_clean_end.endswith("and"):
                                    needs_lookahead = True
                        else:
                            if not re.search(r"[a-zA-Z0-9]", val):
                                needs_lookahead = True

                    if needs_lookahead:
                        lookahead_limit = 8 if field_key in ("built_up_area_sqft", "land_area_sqyd", "built_up_area", "land_area") else 4
                        for offset in range(1, lookahead_limit):
                            if i + offset < len(lines):
                                next_val = lines[i + offset].strip().strip(" |").strip()
                                if next_val:
                                    has_other_label = False
                                    for other_key, other_lbls in FIELD_LABELS.items():
                                        if field_key == "survey_number" and other_key == "property_address":
                                            continue
                                        for ol in other_lbls:
                                            if re.search(rf"(?<!\w){re.escape(ol)}(?!\w)", next_val, flags=re.IGNORECASE):
                                                has_other_label = True
                                                break
                                        if has_other_label:
                                            break
                                    if has_other_label:
                                        break
                                        
                                    if field_key in ("built_up_area_sqft", "land_area_sqyd", "built_up_area", "land_area"):
                                        if re.search(r"\d", next_val):
                                            val = next_val
                                            val_index = i + offset
                                            break
                                    elif field_key == "survey_number":
                                        if re.search(r"\d", next_val):
                                            val = val + " " + next_val
                                            val_index = i + offset
                                            val_clean_end = next_val.strip().lower()
                                            if not (val_clean_end.endswith(",") or val_clean_end.endswith("&") or val_clean_end.endswith("and")):
                                                break
                                        else:
                                            break
                                    else:
                                        val = next_val
                                        val_index = i + offset
                                        break

                    if not val:
                        continue

                    # Field-specific lookahead / cleaners
                    if field_key == "property_address":
                        current_address = val
                        for j in range(val_index + 1, min(len(lines), val_index + 8)):
                            next_line = lines[j].strip()
                            if not next_line:
                                continue
                            if any(re.search(rf"^\s*{re.escape(lbl)}(?!\w)|\b{re.escape(lbl)}\b\s*[:\-–—=]", next_line, flags=re.IGNORECASE) for lbl in [
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
                            
                            if "parking" in next_line.lower() or "whereas" in next_line.lower() or next_line.startswith("/"):
                                is_address_indicator = False
                                
                            if is_address_indicator or has_pincode:
                                next_line = re.sub(r'[-_=]{2,}', ' ', next_line)
                                next_line = re.sub(r'\s+', ' ', next_line).strip()
                                current_address = current_address + " " + next_line
                                if has_pincode:
                                    break
                                if "bound" in next_line.lower() or any(b in next_line.lower().split() for b in ["north", "south", "east", "west"]):
                                    break
                            else:
                                break
                        val = re.sub(r'[-_=]{2,}', ' ', current_address)
                        val = re.sub(r'\s+', ' ', val).strip()

                    elif field_key == "property_description":
                        # Multi-line lookahead for description
                        current_desc = val
                        for j in range(val_index + 1, min(len(lines), val_index + 15)):
                            next_line = lines[j].strip()
                            if not next_line:
                                continue
                            # Stop if we match other sections
                            stop_kws = ["schedule b", "schedule \"b\"", "schedule 'b'", "in witness", "witnesses", "vendor", "vendee", "receipt", "agreement of sale", "work-order", "work order"]
                            if any(kw in next_line.lower() for kw in stop_kws):
                                break
                            
                            # Clean separator lines
                            next_line = re.sub(r'[-_=]{2,}', ' ', next_line)
                            next_line = re.sub(r'\s+', ' ', next_line).strip()
                            if next_line:
                                current_desc = current_desc + "\n" + next_line
                        val = current_desc.strip()

                    elif field_key in ("applicant_name", "owner_name", "purchaser_name", "aos_buyer_name", "aos_seller_name", "wo_party_name"):
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
                                
                                # Smart continuation check
                                nl_lc = next_line.lower()
                                if any(kw in nl_lc for kw in ["aged", "occupation", "r/o", "resident", "pan", "aadhar", "represented", "address", "developer", "builder", "technical", "note", "dimensions", "meters"]):
                                    break
                                    
                                next_line_clean = re.sub(r"\(.*?\)", "", next_line).strip()
                                if next_line_clean:
                                    current_name = current_name + " " + next_line_clean
                                    break
                        val = re.sub(r"\((?:owner|first party|second party|applicant|vendee|vendor|executant|borrower)\)", "", current_name, flags=re.IGNORECASE)
                        val = re.sub(r"\s+(?:aged|about|occup|resident|r/o|resident|pan|aadhar|first party|second party|vendor|vendee|owner|applicant)\b.*", "", val, flags=re.IGNORECASE)
                        val = re.sub(r"\s+", " ", val).strip(" :,-–—=|()").strip()

                    elif field_key == "door_number":
                        if "ptin" in val.lower():
                            idx = val.lower().find("ptin")
                            val = val[:idx].strip()
                        val = val.strip(" :,-–—=|")
                        
                        # Generate ALL door numbers found on the line
                        dns = re.findall(r"\b\d+[-/]\d+[-/]\d+[A-Za-z0-9/-]*\b|\b\d+[-/][A-Za-z0-9/-]+\b", val)
                        if dns:
                            page = find_page_num(line)
                            for dn in dns:
                                candidates.append(Candidate(value=dn, source=label, page=page, score=0, context_line=line, orig_value=dn))
                            continue
                        else:
                            tokens = val.split()
                            if tokens:
                                val = tokens[0]

                    elif field_key == "survey_number":
                        # Clean/truncate survey number at stop words
                        val_lower_v = val.lower()
                        stop_words = ["situated", "under", "admeasuring", "premises", "bearing", "belonging", "flat", "plot", "house", "door", "street", "road", "mandal", "village", "district", "state", "telangana", "ghmc", "old", "new", "east", "west", "north", "south", "bounded"]
                        earliest_idx = len(val)
                        for sw in stop_words:
                            idx = val_lower_v.find(sw)
                            if idx != -1 and idx < earliest_idx:
                                earliest_idx = idx
                        val = val[:earliest_idx].strip(" :,-–—=|()").strip()

                    if not val:
                        continue
                        
                    if field_key in ("built_up_area_sqft", "built_up_area", "land_area_sqyd", "land_area"):
                        nums = re.findall(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", val)
                        if len(nums) > 1:
                            page = find_page_num(line)
                            for num_val in nums:
                                candidates.append(Candidate(value=num_val, source=label, page=page, score=0, context_line=line, orig_value=num_val))
                            continue

                    page = find_page_num(line)
                    candidates.append(Candidate(value=val, source=label, page=page, score=0, context_line=line, orig_value=val))

        # --- 2. CANDIDATE GENERATION (Standalone/Fallback Regexes) ---
        if field_key == "survey_number":
            # Net plot fallback
            net_plot_match = re.search(r"Net Plot Area[^\n]+?(\d+/[A-Z0-9/,-]+(?:\s*,\s*\d+/[A-Z0-9/,-]+)*)", merged_text, flags=re.IGNORECASE)
            if net_plot_match:
                val = re.sub(r"\s+", " ", net_plot_match.group(1)).strip()
                if val:
                    page = find_page_num(net_plot_match.group(0))
                    line_idx = merged_text[:net_plot_match.start()].count('\n')
                    c_line = lines[line_idx] if line_idx < len(lines) else net_plot_match.group(0)
                    candidates.append(Candidate(value=val, source="net_plot_regex", page=page, score=0, context_line=c_line, orig_value=val))
            
            # Standalone survey number regexes
            matches = re.finditer(r"\b\d{1,4}/[A-Z0-9/e\-_]+(?:\s*(?:,|&|and)\s*\d{1,4}/[A-Z0-9/e\-_]+)*\b", merged_text, flags=re.IGNORECASE)
            for m in matches:
                val = m.group(0).strip()
                if val:
                    # check date
                    if re.match(r"^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$", val) or re.match(r"^\d{4}[./-]\d{1,2}[./-]\d{1,2}$", val):
                        continue
                    # check month abbreviations
                    MONTH_ABBRS = {"jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"}
                    val_lower = val.lower()
                    if any(val_lower.startswith(abbr) for abbr in MONTH_ABBRS):
                        continue
                    page = find_page_num(val)
                    line_idx = merged_text[:m.start()].count('\n')
                    c_line = lines[line_idx] if line_idx < len(lines) else val
                    candidates.append(Candidate(value=val, source="standalone_survey_regex", page=page, score=0, context_line=c_line, orig_value=val))
                    
            # And double/ampersand patterns
            matches_amp = re.finditer(r"\b\d{1,4}\s*(?:&|and)\s*\d{1,4}\b", merged_text, flags=re.IGNORECASE)
            for m in matches_amp:
                val = m.group(0).strip()
                page = find_page_num(val)
                line_idx = merged_text[:m.start()].count('\n')
                c_line = lines[line_idx] if line_idx < len(lines) else val
                candidates.append(Candidate(value=val, source="standalone_survey_regex", page=page, score=0, context_line=c_line, orig_value=val))

        elif field_key == "door_number":
            # Standalone door numbers like 17-3-131/B or 17-3-131
            matches = re.finditer(r"\b\d+[-/]\d+[-/]\d+[A-Za-z0-9/-]*\b|\b\d+[-/][A-Za-z0-9/-]+\b", merged_text)
            for m in matches:
                val = m.group(0).strip()
                page = find_page_num(val)
                line_idx = merged_text[:m.start()].count('\n')
                c_line = lines[line_idx] if line_idx < len(lines) else val
                candidates.append(Candidate(value=val, source="standalone_door_regex", page=page, score=0, context_line=c_line, orig_value=val))

        elif field_key in ("built_up_area_sqft", "built_up_area", "land_area_sqyd", "land_area"):
            # Standalone area values like 1200 Sft or 150 Sq Yds (including square meters/meters)
            matches = re.finditer(r"\b\d+(?:,\d{3})*(?:\.\d+)?\s*(?:sft|sq\.?\s*ft|sqft|square\s*feet|sq\.?\s*feet|sq\.?\s*yards?|sqyds?|square\s*yards?|gaj|sq\.?\s*mtrs?|sq\.?\s*meters?|sq\.?\s*mt|sqmt|m2)\b", merged_text, flags=re.IGNORECASE)
            for m in matches:
                val = m.group(0).strip()
                page = find_page_num(val)
                line_idx = merged_text[:m.start()].count('\n')
                c_line = lines[line_idx] if line_idx < len(lines) else val
                candidates.append(Candidate(value=val, source="standalone_area_regex", page=page, score=0, context_line=c_line, orig_value=val))

        elif field_key in ("village", "mandal", "district"):
            # Words near location keywords
            # E.g. [Village name] Village
            matches = re.finditer(r"\b([A-Z][A-Za-z\s']{2,20})\s+(Village|Mandal|District|Dist|Taluka)\b", merged_text, flags=re.IGNORECASE)
            for m in matches:
                val = m.group(1).strip()
                loc_type = m.group(2).lower()
                page = find_page_num(val)
                line_idx = merged_text[:m.start()].count('\n')
                c_line = lines[line_idx] if line_idx < len(lines) else m.group(0)
                candidates.append(Candidate(value=val, source=f"location_{loc_type}_regex", page=page, score=0, context_line=c_line, orig_value=val))
                
            matches_rev = re.finditer(r"\b(Village|Mandal|District)\s+of\s+([A-Z][A-Za-z\s']{2,20})\b", merged_text, flags=re.IGNORECASE)
            for m in matches_rev:
                val = m.group(2).strip()
                loc_type = m.group(1).lower()
                page = find_page_num(val)
                line_idx = merged_text[:m.start()].count('\n')
                c_line = lines[line_idx] if line_idx < len(lines) else m.group(0)
                candidates.append(Candidate(value=val, source=f"location_{loc_type}_regex", page=page, score=0, context_line=c_line, orig_value=val))

            # Extra context matching for "situated at/in", "under/under GHMC"
            matches_sit = re.finditer(r"\b(?:situated at|situated in|under ghmc|under)\s+([A-Z][A-Za-z\s']{2,20})\b", merged_text, flags=re.IGNORECASE)
            for m in matches_sit:
                val = m.group(1).strip()
                page = find_page_num(val)
                line_idx = merged_text[:m.start()].count('\n')
                c_line = lines[line_idx] if line_idx < len(lines) else m.group(0)
                candidates.append(Candidate(value=val, source="location_sit_regex", page=page, score=0, context_line=c_line, orig_value=val))

        elif field_key in ("applicant_name", "owner_name"):
            # Standalone names following Sri/Smt/Mr/Mrs (case-insensitive prefixes)
            matches = re.finditer(r"\b(?:Sri|Smt|Mr|Mrs|Late|SRI|SMT|MR|MRS|LATE)\.?\s*([A-Z][A-Za-z\s'./]{3,60})\b", merged_text)
            for m in matches:
                val = m.group(1).strip()
                page = find_page_num(val)
                line_idx = merged_text[:m.start()].count('\n')
                c_line = lines[line_idx] if line_idx < len(lines) else m.group(0)
                candidates.append(Candidate(value=val, source="standalone_name_regex", page=page, score=0, context_line=c_line, orig_value=val))

        # --- 3. DEDUPLICATE AND RESOLVE TYPES ---
        # Normalize whitespace and clean candidate values
        for c in candidates:
            if isinstance(c.value, str):
                c.value = re.sub(r"\s+", " ", c.value).strip()
                # Clean spaces around commas
                c.value = re.sub(r"\s*,\s*", ", ", c.value)
                
                # Name-specific cleanups
                if field_key in ("owner_name", "applicant_name"):
                    # Strip leading non-alphabetic garbage
                    c.value = re.sub(r"^[^A-Za-z]+", "", c.value)
                    # Strip leading repeat prefixes
                    c.value = re.sub(r"^(?:Sri/Smt\.?|Smt/Sri\.?|Sri\b\.?|Smt\b\.?|Mr\b\.?|Mrs\b\.?|Late\b\.?|\s+)+", "", c.value, flags=re.IGNORECASE)
                    # Strip trailing metadata and non-alphabetic garbage
                    c.value = re.sub(r"\s+(?:a\s+|an\s+)?(?:aged|about|years|occup|resident|r/o|pan|aadhar|first party|second party|vendor|vendee|owner|applicant)\b.*", "", c.value, flags=re.IGNORECASE)
                    # Strip trailing lowercase letter residue
                    c.value = re.sub(r"\s+[a-z]$", "", c.value)
                    c.value = re.sub(r"[^A-Za-z.()]+$", "", c.value)
                    c.value = re.sub(r"\s+", " ", c.value).strip()
                
                if c.orig_value is None:
                    c.orig_value = c.value

        # Helper to find exact candidate char position using its context line if available
        def find_cand_char_idx(c: Candidate, search_val: str) -> int:
            search_val = str(search_val).strip()
            if not search_val:
                return 0
            if c.context_line:
                line_pos = merged_text.lower().find(c.context_line.lower())
                if line_pos != -1:
                    cand_pos_in_line = c.context_line.lower().find(search_val.lower())
                    if cand_pos_in_line != -1:
                        return line_pos + cand_pos_in_line
                    return line_pos
            return find_exact_word_idx(search_val)

        for c in candidates:
            # Type conversions if needed
            if field_key == "built_up_area_sqft":
                char_idx = find_cand_char_idx(c, c.orig_value or str(c.value))
                context_window = ""
                if char_idx != 0:
                    c_start = max(0, char_idx - 150)
                    c_end = min(len(merged_text), char_idx + 150)
                    context_window = merged_text[c_start:c_end]
                if any(kw in merged_text.lower() for kw in ["ghmc", "permit", "municipal", "sanctioned", "corporation", "tsbpass"]):
                    context_window += " ghmc"
                bu_sqft, _ = self._convert_area(c.value, context_window)
                if bu_sqft is not None:
                    c.value = bu_sqft
            elif field_key == "land_area_sqyd":
                char_idx = find_cand_char_idx(c, c.orig_value or str(c.value))
                context_window = ""
                if char_idx != 0:
                    c_start = max(0, char_idx - 150)
                    c_end = min(len(merged_text), char_idx + 150)
                    context_window = merged_text[c_start:c_end]
                if any(kw in merged_text.lower() for kw in ["ghmc", "permit", "municipal", "sanctioned", "corporation", "tsbpass"]):
                    context_window += " ghmc"
                _, la_sqyd = self._convert_area(c.value, context_window)
                if la_sqyd is not None:
                    c.value = la_sqyd

        # --- 4. VALIDATE & RANK CANDIDATES ---
        valid_candidates = []
        for c in candidates:
            val_str = str(c.value)
            # Use orig_value for context lookup if present
            search_val = c.orig_value if c.orig_value else val_str
            
            # Find char position for context
            char_idx = find_exact_word_idx(search_val)
                
            # Snippet of 300 chars around candidate
            context_start = max(0, char_idx - 300)
            context_end = min(len(merged_text), char_idx + len(search_val) + 300)
            context = merged_text[context_start:context_end]
            
            # Find line index and preceding line
            line_idx = -1
            if c.context_line:
                for idx, line in enumerate(lines):
                    if c.context_line == line:
                        line_idx = idx
                        break
            
            cand_line = lines[line_idx] if line_idx != -1 else (c.context_line or "")
            pred_line = lines[line_idx - 1] if (line_idx > 0) else ""
            
            # Perform validation check
            if not self._is_candidate_valid_new(c.value, field_key, context, context_line=cand_line, preceding_line=pred_line, source=c.source):
                continue
                
            # Perform scoring (ranking)
            score = 0
            context_lower = context.lower()
            val_lower = val_str.lower()
            
            if field_key == "survey_number":
                # +10 if found inside Schedule A or Schedule B
                if any(kw in context_lower for kw in ["schedule a", "schedule b", "schedule of", "schedule"]):
                    score += 10
                # +5 if found near: "All that piece and parcel", "situated at"
                if any(kw in context_lower for kw in ["all that piece and parcel", "situated at", "situated in"]):
                    score += 5
                # +3 if contains "/"
                if "/" in val_lower:
                    score += 3
                # +2 if contains "&"
                if "&" in val_lower or "and" in val_lower:
                    score += 2
                # +2 if appears multiple times
                if merged_text.lower().count(val_lower) > 1:
                    score += 2
                # +2 if found later in document
                if char_idx > len(merged_text) / 2:
                    score += 2
                    
            elif field_key == "door_number":
                # +5 if contains "-"
                if "-" in val_lower:
                    score += 5
                # +2 if contains "/"
                if "/" in val_lower:
                    score += 2
                # +3 if near flat/premise keywords
                if any(kw in context_lower for kw in ["flat", "premise", "house", "plot", "villa", "apartment", "h.no", "door", "d.no", "h no", "d no"]):
                    score += 3
                # +2 if appears multiple times
                if merged_text.lower().count(val_lower) > 1:
                    score += 2
                # +2 if found later in document
                if char_idx > len(merged_text) / 2:
                    score += 2
                # +5 if "new" is within 15 characters after the value in context
                # Find the position of search_val in context
                val_pos = context_lower.find(search_val.lower())
                if val_pos != -1:
                    after_val = context_lower[val_pos + len(search_val) : val_pos + len(search_val) + 15]
                    if "new" in after_val:
                        score += 5
                # +2 if the candidate has a slash/letter suffix (e.g. 17-3-131/B)
                if re.search(r"/[A-Za-z0-9]+$", val_lower):
                    score += 2
                    
            elif field_key in ("built_up_area_sqft", "built_up_area"):
                # Prefer matches near built up area labels
                if any(kw in context_lower for kw in ["built up area", "built-up area", "admeasuring"]):
                    score += 5
                if any(u in val_lower for u in ["sft", "sq ft", "sqft", "square feet"]):
                    score += 5
                if any(kw in context_lower for kw in ["area", "built-up", "land"]):
                    score += 3
                if "excluding parking" in context_lower:
                    score += 5
                if "including parking" in context_lower:
                    score -= 5
                    
            elif field_key in ("land_area_sqyd", "land_area"):
                if any(kw in context_lower for kw in ["land area", "schedule a", "admeasuring"]):
                    score += 5
                if any(u in val_lower for u in ["sq yd", "sqyd", "sq yds", "square yard", "square yards", "gaj"]):
                    score += 5
                if any(kw in context_lower for kw in ["area", "built-up", "land", "extent"]):
                    score += 3
                if "excluding parking" in context_lower:
                    score += 5
                if "including parking" in context_lower:
                    score -= 5
                    
            elif field_key == "village":
                # Prefer candidates inside Schedule A
                if "schedule a" in context_lower:
                    score += 10
                if any(kw in context_lower for kw in ["village", "mandal", "district", "situated at"]):
                    score += 5
                if "situated at" in context_lower or "situated in" in context_lower:
                    score += 3
                if "village" in context_lower:
                    score += 4
                # Preceding syntax bonus
                val_pos = context_lower.find(val_lower)
                if val_pos > 0:
                    pre_ctx = context_lower[max(0, val_pos - 20) : val_pos]
                    if any(kw in pre_ctx for kw in ["situated at", "situated in", "site at", "village"]):
                        score += 5
                if c.source == "location_village_regex" or any(c.source.lower().startswith(l.lower()) for l in FIELD_LABELS["village"]):
                    score += 10
                    
            elif field_key in ("mandal", "district"):
                if any(kw in context_lower for kw in ["village", "mandal", "district", "situated at"]):
                    score += 5
                if "situated at" in context_lower or "situated in" in context_lower:
                    score += 3
                if field_key == "mandal":
                    if "mandal" in context_lower or "tahsil" in context_lower or "taluka" in context_lower:
                        score += 4
                    val_pos = context_lower.find(val_lower)
                    if val_pos > 0:
                        pre_ctx = context_lower[max(0, val_pos - 20) : val_pos]
                        if any(kw in pre_ctx for kw in ["under ghmc", "under", "mandal", "tahsil", "taluka"]):
                            score += 5
                    if c.source == "location_mandal_regex" or any(c.source.lower().startswith(l.lower()) for l in FIELD_LABELS["mandal"]):
                        score += 10
                elif field_key == "district":
                    if "district" in context_lower or "dist" in context_lower:
                        score += 4
                    val_pos = context_lower.find(val_lower)
                    if val_pos > 0:
                        pre_ctx = context_lower[max(0, val_pos - 20) : val_pos]
                        if "district" in pre_ctx or "dist" in pre_ctx:
                            score += 5
                    if c.source == "location_district_regex" or any(c.source.lower().startswith(l.lower()) for l in FIELD_LABELS["district"]):
                        score += 10
                    
            elif field_key == "owner_name":
                if any(kw in context_lower for kw in ["first party", "owner", "land owner", "executant", "vendor"]):
                    score += 5
                if any(kw in context_lower for kw in ["second party", "vendee", "purchaser", "buyer", "in favour of"]):
                    score -= 5
                if any(kw in val_lower or kw in context_lower for kw in ["sri", "smt", "mr", "mrs", "late"]):
                    score += 3
                # Capitalized check
                words = val_str.split()
                if words and all(w[0].isupper() for w in words if w.isalpha()):
                    score += 2
                    
            elif field_key == "applicant_name":
                if any(kw in context_lower for kw in ["second party", "vendee", "in favour of", "applicant", "purchaser", "buyer", "allotted to", "allotted the", "received from", "received a sum", "favor of vendee"]):
                    score += 5
                if any(kw in context_lower for kw in ["first party", "owner", "land owner", "landowner", "vendor", "executant"]):
                    score -= 5
                if any(kw in val_lower or kw in context_lower for kw in ["sri", "smt", "mr", "mrs", "late"]):
                    score += 3
                words = val_str.split()
                if words and all(w[0].isupper() for w in words if w.isalpha()):
                    score += 2
                    
            elif field_key == "property_address":
                if re.search(r"\b\d{6}\b|\b5[oO\d]{5}\b", val_str):
                    score += 5
                if any(kw in val_lower for kw in ["road", "street", "lane", "nagar", "colony", "flat", "apartment", "h.no", "plot"]):
                    score += 3
                if any(kw in context_lower for kw in ["situated at", "situated in", "schedule", "property"]):
                    score += 3
                if any(kw in val_lower for kw in ["mandal", "district", "dist", "state", "telangana"]):
                    score += 4
                if "schedule a" in context_lower or "schedule b" in context_lower or "schedule of" in context_lower:
                    score += 3
                # Penalty for personal residence labels/contexts
                if c.source in ["Resident of", "R/o.", "R/o"] or any(val_lower.startswith(prefix) for prefix in ["resident of", "r/o"]):
                    score -= 10
                    
            elif field_key == "property_description":
                if any(kw in context_lower for kw in ["schedule a", "schedule b", "schedule of"]):
                    score += 10
                # Add a big bonus if the value itself contains boundary keywords
                if any(kw in val_lower for kw in ["north", "south", "east", "west", "bounded", "boundary", "boundaries"]):
                    score += 15
                    
            c.score = score
            valid_candidates.append(c)

        # --- 5. SELECT BEST CANDIDATE ---
        if not valid_candidates:
            return {
                "value": None,
                "source_page": None,
                "ocr_confidence": 0.0,
                "regex_confidence": 0.0,
                "final_confidence": 0.0,
                "validation_status": "valid",
                "validation_message": None
            }

        # Sort by score first, then fallback to OCR confidence
        valid_candidates.sort(key=lambda x: (x.score, get_ocr_conf(str(x.value), x.page)), reverse=True)
        
        # Deduplicate values after sorting, keeping the highest scoring candidates
        seen_vals = set()
        dedup_candidates = []
        for c in valid_candidates:
            val_key = str(c.value).lower().strip()
            if val_key not in seen_vals:
                seen_vals.add(val_key)
                dedup_candidates.append(c)
        valid_candidates = dedup_candidates

        # Deduplicate substrings for name fields
        if field_key in ("owner_name", "applicant_name"):
            valid_candidates.sort(key=lambda x: len(str(x.value)), reverse=True)
            temp = []
            for c in valid_candidates:
                val_str = str(c.value)
                if not any(val_str in str(ac.value) for ac in temp):
                    temp.append(c)
            valid_candidates = temp

        if not valid_candidates:
            return {
                "value": None,
                "source_page": None,
                "ocr_confidence": 0.0,
                "regex_confidence": 0.0,
                "final_confidence": 0.0,
                "validation_status": "valid",
                "validation_message": None
            }

        # Re-sort to ensure best is first
        valid_candidates.sort(key=lambda x: (x.score, get_ocr_conf(str(x.value), x.page)), reverse=True)
        best = valid_candidates[0]
        
        ocr_conf = get_ocr_conf(str(best.value), best.page)
        regex_conf = min(1.0, 0.5 + (best.score / 20.0))
        final_conf = (0.7 * ocr_conf) + (0.3 * regex_conf)
        
        return {
            "value": best.value,
            "source_page": best.page,
            "ocr_confidence": float(ocr_conf),
            "regex_confidence": float(regex_conf),
            "final_confidence": float(final_conf),
            "validation_status": "valid",
            "validation_message": None
        }

    # Helper method for validation
    def _is_candidate_valid_new(
        self,
        val: Any,
        field_key: str,
        context: str,
        context_line: str | None = None,
        preceding_line: str | None = None,
        source: str | None = None
    ) -> bool:
        if val is None:
            return False
        
        val_str = str(val).strip()
        if not val_str:
            return False
        
        val_lower = val_str.lower()
        context_lower = context.lower()
        
        if not re.search(r"[a-zA-Z0-9]", val_str):
            return False
            
        if field_key == "survey_number":
            if not re.search(r"\d", val_str):
                return False
            # Reject if contains a 4-digit year like /2024 or /2023 or 2010
            if re.search(r"\b(?:19|20)\d{2}\b", val_lower):
                return False
            if re.search(r"/[12]\d{3}\b", val_lower):
                return False
            if any(kw in val_lower for kw in ["village", "mandal", "district", "hyderabad", "state"]):
                return False
            if re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", val_lower):
                return False
            if re.search(r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b", val_lower):
                return False
                
            # Reject license/technical person indicators
            if any(kw in val_lower for kw in ["engg", "stri", "ltp", "lic", "license", "arch", "technical", "struct"]):
                return False
            
            # Check context line and candidate line for technical person labels
            lines_to_check = []
            if context_line:
                lines_to_check.append(context_line.lower())
            if preceding_line:
                lines_to_check.append(preceding_line.lower())
            
            tech_kws = ["structural", "engineer", "technical person", "architect", "lic.no", "license", "builder", "developer"]
            for line_lc in lines_to_check:
                if any(kw in line_lc for kw in tech_kws):
                    return False
                    
            # Reject if candidate is part of a larger door number or hyphenated/numeric string
            if val_str and context:
                idx = context.lower().find(val_lower)
                if idx > 0:
                    pre_char = context[idx - 1]
                    if pre_char == "-" or pre_char.isdigit() or pre_char == "/":
                        return False

            # Reject if candidate is on a line that describes boundaries
            # or immediately follows a line with a boundary keyword
            lines_in_ctx = [line.strip().lower() for line in context.split('\n') if line.strip()]
            for j, l in enumerate(lines_in_ctx):
                if val_lower in l:
                    is_boundary = False
                    for b_kw in ["north", "south", "east", "west", "boundary", "boundaries", "bounded", "bounds"]:
                        if b_kw in l:
                            if l.startswith(b_kw) or "bound" in l:
                                is_boundary = True
                                break
                        if j > 0 and b_kw in lines_in_ctx[j - 1]:
                            pre_l = lines_in_ctx[j - 1]
                            if pre_l in ("north", "south", "east", "west", "boundary", "boundaries") or pre_l.startswith(b_kw):
                                is_boundary = True
                                break
                    if is_boundary:
                        return False
                
        elif field_key == "door_number":
            if any(kw in val_lower for kw in ["village", "mandal", "district", "taluka", "state"]):
                return False
            if any(kw in val_lower for kw in ["feet", "sqft", "yards", "sqyd", "sft"]):
                return False
            if "ptin" in val_lower:
                return False
            if len(val_str) > 30:
                return False
                
        elif field_key in ("built_up_area_sqft", "built_up_area"):
            if not re.search(r"\d", val_str):
                return False
            
            # Reject if context contains cool roof/boilerplate policy keywords
            if any(kw in context_lower or kw in (context_line or "").lower() for kw in ["cool roof", "policy", "shall comply", "comply with", "mandatory for", "threshold"]):
                return False
                
            # Reject if UDS keywords immediately precede the number (within 35 chars)
            if context:
                # Use orig_value if present to find position in context
                orig_val = val_str
                # Search for original val in context
                idx = context.lower().find(orig_val.lower())
                if idx == -1 and "." in orig_val:
                    # try without .0 suffix if float
                    orig_val_clean = orig_val.split(".")[0]
                    idx = context.lower().find(orig_val_clean.lower())
                if idx != -1:
                    pre_text = context[max(0, idx - 35) : idx].lower()
                    if any(kw in pre_text for kw in ["undivided", "uds", "share of land"]):
                        return False
            
            # Reject if context has explicit carpet/balcony area markers, not just general occurrences
            lines_to_check = []
            if context_line:
                lines_to_check.append(context_line.lower())
            if preceding_line:
                lines_to_check.append(preceding_line.lower())
                
            # Reject built_up_area candidates if the candidate line or preceding line contains land keywords
            land_rejects = ["land area", "plot area", "extent of land", "net plot", "undivided share", "uds", "share of land"]
            if context_line and any(kw in context_line.lower() for kw in land_rejects):
                return False
            if preceding_line and any(kw in preceding_line.lower() for kw in land_rejects):
                cand_line_lower = (context_line or "").lower()
                if not any(kw in cand_line_lower for kw in ["built up", "built-up", "builtup"]):
                    return False
                    
            for line_lc in lines_to_check:
                if re.search(r"\b(?:carpet|balcony)\s*area\b", line_lc):
                    return False
            if "carpet area" in context_lower or "balcony area" in context_lower:
                return False

            # Restrict fee blacklisting to candidate line and preceding line with word boundary
            fee_kws = ["fee", "fees", "charge", "charges", "deposit", "payment", "cess", "tax", "rs.", "rupees"]
            for line_lc in lines_to_check:
                if any(re.search(rf"\b{re.escape(kw)}\b", line_lc) for kw in fee_kws):
                    return False
                    
            # Reject if the original matched value itself contains boilerplate clauses
            if any(kw in val_lower for kw in ["shall", "should", "will", "services", "sanitation", "plumbing", "mortgage", "authority", "financial"]):
                return False
            try:
                num = float(val_str)
                if num <= 50.0 or num > 100000.0:
                    return False
            except ValueError:
                pass
                
        elif field_key in ("land_area_sqyd", "land_area"):
            if not re.search(r"\d", val_str):
                return False
            
            # Reject if context contains cool roof/boilerplate policy keywords
            if any(kw in context_lower or kw in (context_line or "").lower() for kw in ["cool roof", "policy", "shall comply", "comply with", "mandatory for", "threshold"]):
                return False
                
            # Reject if UDS keywords immediately precede the number (within 35 chars)
            if context:
                orig_val = val_str
                idx = context.lower().find(orig_val.lower())
                if idx == -1 and "." in orig_val:
                    orig_val_clean = orig_val.split(".")[0]
                    idx = context.lower().find(orig_val_clean.lower())
                if idx != -1:
                    pre_text = context[max(0, idx - 35) : idx].lower()
                    if any(kw in pre_text for kw in ["undivided", "uds", "share of land"]):
                        return False
            
            # Reject if context has explicit carpet/balcony area markers
            lines_to_check = []
            if context_line:
                lines_to_check.append(context_line.lower())
            if preceding_line:
                lines_to_check.append(preceding_line.lower())
                
            # Reject land_area candidates if the candidate line or preceding line contains built-up keywords
            built_up_rejects = ["built up", "built-up", "builtup", "flat area", "flat no", "balcony", "carpet", "terrace", "stilt"]
            if context_line and any(kw in context_line.lower() for kw in built_up_rejects):
                return False
            if preceding_line and any(kw in preceding_line.lower() for kw in built_up_rejects):
                cand_line_lower = (context_line or "").lower()
                if not any(kw in cand_line_lower for kw in ["land area", "plot area", "extent of land", "net plot", "area of plot"]):
                    return False
                    
            for line_lc in lines_to_check:
                if re.search(r"\b(?:carpet|balcony)\s*area\b", line_lc):
                    return False
            if "carpet area" in context_lower or "balcony area" in context_lower:
                return False

            # Restrict fee blacklisting to candidate line and preceding line with word boundary
            fee_kws = ["fee", "fees", "charge", "charges", "deposit", "payment", "cess", "tax", "rs.", "rupees"]
            for line_lc in lines_to_check:
                if any(re.search(rf"\b{re.escape(kw)}\b", line_lc) for kw in fee_kws):
                    return False
                    
            if any(kw in val_lower for kw in ["shall", "should", "will", "services", "sanitation", "plumbing", "mortgage", "authority", "financial"]):
                return False
            try:
                num = float(val_str)
                if num <= 10.0 or num > 50000.0:
                    return False
            except ValueError:
                pass
                
        elif field_key in ("village", "mandal", "district"):
            if re.search(r"^\d+$", val_str):
                return False
            
            # Clean and strip surrounding punctuation/whitespace
            val_clean = re.sub(r"^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$", "", val_str).strip()
            val_clean_lower = val_clean.lower()
            
            if val_clean_lower in ["ts", "t.s", "tg", "ap", "a.p.", "telangana", "state", "india", "mandal", "village", "district", "district,"]:
                return False
            if len(val_clean) < 3 or len(val_clean) > 35:
                return False
            if re.search(r"^\d", val_clean):
                return False
            if any(kw in val_clean_lower for kw in ["sri", "smt", "mr", "mrs", "late"]):
                return False
                
            # Reject if contains structural/boundary keywords
            loc_reject_anywhere = ["locality", "name", "plot", "street", "road", "house", "door", "no", "flat", "apartment", "premises", "boundary", "north", "south", "east", "west", "sign", "signature", "officer", "licensed", "ghmc", "hmda", "parking", "town", "city", "municipal", "corporation", "permit", "file"]
            if any(w in val_clean_lower.split() for w in loc_reject_anywhere):
                return False
                
            # Reject running text clauses/grammar
            location_reject_words = ["and", "which", "more", "fully", "described", "in", "the", "referred", "herein", "after", "called", "of", "to", "by", "for", "with"]
            if any(kw in val_clean_lower.split() for kw in location_reject_words):
                return False
            # Reject based on mismatching location type sources
            if source:
                if field_key == "village" and any(x in source for x in ["mandal", "district", "dist_", "taluka"]):
                    return False
                elif field_key == "mandal" and any(x in source for x in ["village", "district", "dist_"]):
                    return False
                elif field_key == "district" and any(x in source for x in ["village", "mandal", "taluka"]):
                    return False
            # Reject if value itself contains other location keywords
            if field_key == "village" and any(kw in val_clean_lower for kw in ["mandal", "district", "taluka", "state"]):
                return False
            elif field_key == "mandal" and any(kw in val_clean_lower for kw in ["village", "district", "state"]):
                return False
            elif field_key == "district" and val_clean_lower in ["telangana state", "telangana", "state", "andhra pradesh", "ap state"]:
                return False
                
            location_reject_kws = ["issued", "reg", "approved", "certified", "signed", "subject", "clause", "page", 
                                   "belonging", "under", "strict", "supervision", "accordance", "hereby", "sanctioned",
                                   "conditions", "permit", "file", "date", "construction", "proposed", "building"]
            if any(kw in val_clean_lower for kw in location_reject_kws):
                return False
            elif field_key == "district" and val_clean_lower in ["telangana state", "telangana", "state", "andhra pradesh", "ap state"]:
                return False
                
            location_reject_kws = ["issued", "reg", "approved", "certified", "signed", "subject", "clause", "page", 
                                   "belonging", "under", "strict", "supervision", "accordance", "hereby", "sanctioned",
                                   "conditions", "permit", "file", "date", "construction", "proposed", "building"]
            if any(kw in val_clean_lower for kw in location_reject_kws):
                return False
                
        elif field_key in ("owner_name", "applicant_name", "purchaser_name", "aos_buyer_name", "aos_seller_name", "wo_party_name"):
            if sum(1 for char in val_str if char.isdigit()) > 3:
                return False
            # Names should not contain common boilerplate words
            name_reject_kws = ["shall", "ensure", "safety", "construction", "workers", "signature", "commencement", 
                               "building", "submitted", "hereby", "accorded", "revoked", "permit", "payment",
                               "agree", "agrees", "execute", "transferred", "hereinafter", "referred", "witness", "deed", "address",
                               "plan", "sanctioned", "accordance", "supervision", "architect", "engineer", "structural", "site", 
                               "development", "corporation", "commissioner", "officer", "authority", "municipal", "zonal", 
                               "government", "clearance", "order", "permit", "regulation", "conditions", "general", "special", 
                               "additional", "technical", "personnel", "licence", "license", "registration", "document", "office"]
            if any(kw in val_lower for kw in name_reject_kws):
                return False
            if field_key == "applicant_name":
                if any(kw in val_lower for kw in ["road", "colony", "nagar", "village", "h.no"]):
                    return False
            if len(val_str) > 80:
                return False
                
        elif field_key == "property_address":
            if len(val_str) > 250:
                return False
            if len(val_str) < 10:
                return False
                
        elif field_key in ("purchaser_phone", "applicant_phone", "owner_phone"):
            digits_only = re.sub(r"\D", "", val_str)
            if len(digits_only) < 10 or len(digits_only) > 15:
                return False
                
        elif field_key == "property_description":
            if len(val_str) < 15:
                return False
            if any(word in val_lower for word in ["now this deed", "in witness whereof", "shall govern"]):
                return False
            # Reject joinery or other tables
            if any(word in val_lower or word in context_lower for word in ["joinery", "doors", "windows", "collapsible"]):
                return False
                
        return True
