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
    

    # ─── PARTIES ───────────────────────────────────────────────────────────────
    "name_of_the_owner_s": [
        "Name of Owner", "Name of the Owner", "Name of the Owner(s)",
        "Owner Name", "Owner's Name", "Owners Name", "Name of Owners",
        "Applicant Name", "Borrower Name", "Mortgagor Name",
        "Land Owner Name", "Property Owner", "Title Holder",
        "Name of Proprietor", "Vendor Name", "First Party Name",
        "Land Owner", "Owner / Applicant", "Malik Ka Naam",
        "Bhu Swami", "Bhuswami", "Swami Ka Naam",
        "Name of the Vendor", "Seller Name", "Grantor Name",
        "Name of Applicant", "Customer Name", "Account Holder Name",
        "Naame of Owner", "Nmae of Owner", "Ownr Name",
        "Owenr Name", "Nam of Owner", "Onwer Name",
        # AOS-specific
        "First Party", "Land Owner / Vendor", "Vendor",
        "Name of the First Party", "FIRST PARTY / LAND OWNER / VENDOR",
        "Absolute Owner", "Peaceful Possessor",
        "W/o", "S/o", "D/o", "H/o",  # relation prefixes often parsed as labels
    ],

    "purchaser_name": [
        "Name of Purchaser", "Name of the Purchaser", "Purchaser Name",
        "Name of the Purchaser(s)", "Vendee Name", "Buyer Name",
        "Name of Buyer", "Name of Vendee", "Second Party Name",
        "Allottee Name", "Name of Allottee", "Transferee Name",
        "Name of Transferee", "Name of Borrower", "Loan Applicant",
        "Name of Applicant", "Co-Applicant Name", "Name of Co-Applicant",
        "Khareedaar Ka Naam", "Krideta", "Purchaser / Vendee",
        "Purchasr Name", "Purchaser Nmae", "Puchaser Name",
        # AOS-specific
        "Vendee", "IN FAVOUR OF", "In Favour Of", "In favor of",
        "Name of the Vendee", "VENDEE", "Purchaser / Allottee",
        "Second Party", "Name of Second Party",
    ],

    "developer_name": [
        "Developer Name", "Name of Developer", "Builder Name",
        "Name of Builder", "Promoter Name", "Name of Promoter",
        "Contractor Name", "Second Party", "Developer / Builder",
        "Construction Company", "Project Developer", "Society Name",
        "Name of Society", "Housing Society", "Nirman Karta",
        # AOS/WO-specific
        "Developer / Second Party", "DEVELOPER", "Name of the Developer",
        "M/s", "M/S", "Company Name", "Pvt Ltd", "Private Limited",
        "Second Party(ies)", "SECOND PARTY(IES)/CONTRACTOR(S)",
        "Contractor", "Registered Company", "Company",
        "Rep. by its Manager", "Authorised Signatory", "Authorized Signatory",
    ],

    "vendor_name": [
        "Vendor Name", "Name of Vendor", "Seller", "First Party",
        "Grantor", "Transferor", "Seller Name", "Vikretha",
        "Vikreta Ka Naam",
        # AOS-specific
        "VENDOR", "Vendor", "Land Owner / Vendor",
        "FIRST PARTY / LAND OWNER / VENDOR",
        "Sole Owner", "Absolute Owner and Peaceful Possessor",
        "Name of Land Owner",
    ],

    "power_of_attorney_holder": [
        "Power of Attorney Holder", "POA Holder", "GPA Holder",
        "General Power of Attorney Holder", "Attorney Holder",
        "Authorized Signatory", "Authorised Signatory",
        "PA Holder", "Attorney Name", "Agent Name",
        "Power of Attorney", "GPA", "GPOA",
        # AOS-specific
        "Development Agreement cum General Power of Attorney Holder",
        "DA cum GPA Holder", "REPRESENTED BY HER DEVELOPMENT AGREEMENT",
        "Rep. by Manager", "Manager", "Represented By",
        "Development Agreement cum GPA", "DA-GPA Holder",
        "Rep. by its Manager",
    ],

    "relation": [
        "W/o", "S/o", "D/o", "H/o", "C/o",
        "Wife of", "Son of", "Daughter of", "Husband of",
        "Care of", "Relative of",
        "Late", "L/o",
    ],

    "witness_1": [
        "Witness 1", "Witness No. 1", "First Witness", "Sakshi 1",
        "Gawah 1", "Witness-1", "W1", "Witness Name 1",
        "WITNESSES: 1", "Witnesses 1.", "Witnesss 1",
    ],

    "witness_2": [
        "Witness 2", "Witness No. 2", "Second Witness", "Sakshi 2",
        "Gawah 2", "Witness-2", "W2", "Witness Name 2",
        "WITNESSES: 2", "Witnesses 2.", "Witnesss 2",
    ],

    "aadhar_number": [
        "Aadhar No", "Aadhaar No", "Aadhar Number", "Aadhaar Number",
        "UIDAI No", "UID No", "Aadhar Card No", "Aadhaar Card Number",
        "Aadhar No.", "AADHAR NO", "AADHAAR NO", "Adhar No",
        "Aadhar ID", "UID", "Unique ID", "Aadhar", "Aadhaar",
        # AOS-specific OCR patterns
        "AADHAR NO:", "Aadhaar No.", "Aadhaar No:",
        "Aadhar No :", "(AADHAR NO:", "(Aadhaar No.",
        "Aadhar Number:", "UIDAI Number",
    ],

    "pan_number": [
        "PAN No", "PAN Number", "PAN Card No", "Permanent Account Number",
        "PAN No.", "PAN", "IT PAN", "Income Tax PAN",
        "PAN Card Number", "PAN-No", "PAN Num",
        "(PAN No.", "(PAN No:", "PAN No:", "PAN No :",
        "PAN Number:", "PAN Card No:",
    ],

    "age": [
        "Age", "Aged About", "Age of Person", "Date of Birth",
        "DOB", "Age (Years)", "Age in Years",
        "aged about", "Aged about", "aged",
        "years", "Age:", "Age :",
    ],

    "occupation": [
        "Occupation", "Profession", "Vyavsay", "Occupation/Profession",
        "Nature of Work", "Employment", "Job",
        "Occupation:", "Occupation :", "Business",
        "Pvt Employee", "Private Employee", "Government Employee",
        "Self Employed", "Retired", "Housewife",
    ],

    "cell_number": [
        "Cell", "Cell No", "Mobile", "Mobile No", "Phone No",
        "Contact No", "Mobile Number", "Phone Number",
        "Cell Number", "Contact Number", "Tel No", "Telephone No",
        "Ph No", "Mob No", "Contact", "Mobile / Phone",
        "Cell:", "Cell No:", "Cell No.",
        "Cell: 8008806408",  # OCR may pick up value inline
    ],

    "residential_address": [
        "Residential Address", "Address", "R/o", "Resident of",
        "Permanent Address", "Home Address", "Residing at",
        "Address of Owner", "Address of Applicant",
        "House Address", "Current Address", "Present Address",
        "Correspondence Address", "Niwas Sthal",
        "Resident of", "Residing at", "R/o.",
        "Address of Vendee", "Address of Vendor",
        "Residing", "Resident", "Resides at",
        "H. No.", "H No", "House No",
    ],

    # ─── PROPERTY IDENTIFICATION ───────────────────────────────────────────────
    "survey_no": [
        "Survey No", "Survey No.", "Survey Number", "Sy No",
        "Sy. No", "Survey Nos", "S.No", "S. No.",
        "Svy No", "Khasra No", "Khasra Number", "Plot Survey No",
        "Survey / Khasra No", "Dag No", "Daag No",
        "Bhoomi Survey No", "Field No", "Gunta No",
        "Hissa No", "Sub-Division No", "RS No", "TS No",
        "Revenue Survey No", "Sruvey No", "Survay No",
        "Survy No", "Survey N0",
        # AOS-specific
        "Survey Nos.", "Survey Nos", "in Survey Nos.",
        "Survey Nos. 90", "Sy Nos", "Survey No 90",
        "Survey No. 90", "Survey Nos.90",
        "90/ఄ", "92/ఄ",  # Telugu script survey numbers
    ],

    "plot_no": [
        "Plot No", "Plot No.", "Plot Number", "Plot Nos",
        "Door No", "Door No.", "House No", "House Number",
        "Door No / House No", "Door / House No",
        "Municipal No", "Municipal Door No", "Property No",
        "Flat No", "Unit No", "Shop No", "Site No",
        "Block No", "Lot No", "Premises No",
        "Bhukhand Sankhya", "Khasra Plot No",
        "Plt No", "Plto No", "Door Noo", "H No", "H. No",
        # AOS-specific
        "Door No.17-3-131", "Door No.17-3-131/B",
        "Door No 17-3-131", "Premises bearing Door No",
        "Municipal Premises Door No", "Municipal Premises",
        "Premises Door No", "Door No (Old)", "Door No (New)",
        "Old PTIN", "New PTIN",
    ],

    "ptin_no": [
        "PTIN No", "PTIN", "PTIN Number", "Property Tax ID",
        "Property Tax Identification No", "Tax ID No",
        "GHMC PTIN", "Municipal PTIN", "Patta No",
        # AOS-specific
        "PTIN No.", "PTIN:", "PTIN No:",
        "PTIN: 1220310604", "PTIN: 1221700489",
        "PTIN (Old)", "PTIN (New)", "Old PTIN", "New PTIN",
    ],

    "t_s_no_village": [
        "T.S. No", "T.S. No.", "TS No", "TS Number",
        "T.S. No / Village", "Village", "Village Name",
        "Gram", "Gaon", "Panchayat Village",
        "Revenue Village", "Mandal / Village", "Hobli",
        "T S No", "TS No / Village", "Township Survey No",
        "Town Survey No", "Municipal Survey No",
        "T.S No", "T.S.No", "TS. No",
        # AOS-specific
        "situated at", "Situated at", "situated at BANDLAGUDA",
        "Location", "Place", "Locality Name",
    ],

    "ward_taluka": [
        "Ward", "Taluka", "Ward / Taluka", "Ward/Taluka",
        "Taluk", "Tehsil", "Tahsil", "Tahasil",
        "Ward No", "Ward Number", "Revenue Taluka",
        "Mandal", "Circle", "Zone", "Division",
        "Municipal Ward", "Corporation Ward",
        "Wrd / Taluka", "Ward / Taluk",
        # AOS-specific
        "under GHMC", "GHMC", "GHMC Ramachandrapuram",
        "under GHMC Ramachandrapuram",
    ],

    "mandal_district": [
        "Mandal", "District", "Mandal / District", "Mandal/District",
        "Dist", "Dist.", "Revenue District", "Revenue Mandal",
        "Mandal Name", "District Name", "Zila",
        "Zilah", "Jilla", "Revenue Circle",
        "Tehsil / District", "Block / District",
        "Mandal / Dist", "Mandal-District",
        # AOS-specific
        "Sanga Reddy District", "Sangareddy District",
        "Sangareddy Dt", "Sangareddy", "Sanga Reddy",
        "K.V.Rangareddy District", "Rangareddy District",
        "Rangareddy Dt", "Medak", "Medak TG",
    ],

    "city_town": [
        "City", "City / Town", "Town", "City/Town",
        "Municipality", "Municipal Area", "Corporation",
        "Urban Area", "Nagar", "Sheher",
        "Gram Panchayat", "Taluk HQ", "District HQ",
        "City Name", "Town Name", "Locality",
        "Cty / Town", "Cit / Town",
        # AOS-specific
        "Hyderabad", "Bandlaguda", "BANDLAGUDA",
        "Narsingi", "Puppalaguda", "Patancheru",
        "Kokapet", "Goshala",
    ],

    "postal_address_of_the_property": [
        "Postal Address of the Property", "Property Address",
        "Address of Property", "Address of the Property",
        "Site Address", "Flat Address", "House Address",
        "Location Address", "Property Location",
        "Registered Address", "Situated At",
        "Postal Address", "Full Address",
        "Complete Address", "Asset Address",
        "Sampatti Ka Pata", "Postal Adress",
        "Proprty Address", "Addres of Property",
        # AOS-specific
        "situated at BANDLAGUDA", "Premises bearing",
        "in Premises bearing", "in Survey Nos.",
        "under GHMC Ramachandrapuram",
        "Sanga Reddy District, Telangana State",
        "Telangana State", "Telangana",
    ],

    "flat_no": [
        "Flat No", "Flat No.", "Flat Number", "Unit No",
        "Unit Number", "Apartment No", "Apartment Number",
        "Flat / Unit No", "Flat Nos", "Flat No (East)",
        "Flat No (West)", "Flat No (North)", "Flat No (South)",
        # AOS-specific
        "Semi-Finished Flat No.", "Semi-Finished Flat No",
        "Flat No.502", "Flat No.502(EAST)", "Flat 502",
        "Flat No 502", "Unit 502", "Flat No.502 (EAST)",
        "Semi-Finished Flat", "Flat No(East)", "Flat No(West)",
    ],

    "building_name": [
        "Building Name", "Project Name", "Name of Building",
        "Name of Project", "Apartment Name", "Complex Name",
        "Society Name", "Colony Name", "Layout Name",
        "Housing Project", "Scheme Name", "Tower Name",
        # AOS-specific
        "GBR Barcelona", "\"GBR Barcelona\"",
        "building names as", "building named as",
        "the building names as", "Residential Complex",
        "Name of Complex", "Project",
    ],

    "floor_no": [
        "Floor No", "Floor Number", "Floor", "Level",
        "Storey", "Floor / Level", "Ground Floor",
        "Stilt Floor", "Upper Floor", "Basement",
        "G+F", "Floor Nos",
        # AOS-specific
        "5th Floor", "5th floor", "Fifth Floor",
        "Stilt / Parking + Upper 5 Floors",
        "Stilt + Upper 5 Floors",
        "Upper 5 Floors",
        "G+5", "G + 5", "Stilt+5",
    ],

    "property_description": [
        "Brief Description of Property", "Description of Property",
        "Property Description", "Brief Description",
        "Property Details", "Asset Description",
        "Description of the Property", "Schedule of Property",
        "Schedule Property", "Property Particulars",
        "Nature of Property", "Type of Property",
        "Sampatti Ka Vivaran", "Description",
        "Proprty Description", "Descripton of Property",
        # AOS-specific
        "Open Plot", "Open Land Municipal Premises",
        "All that the", "All that the Open Land",
        "Semi-Finished Flat", "Residential Apartment",
        "Residential Complex",
    ],

    "schedule_of_property": [
        "Schedule of Property", "Schedule A Property",
        "Schedule B Property", "Schedule 'A'", "Schedule 'B'",
        "Schedule A", "Schedule B", "Property Schedule",
        "Schedule of the Property", "Anusoochi",
        "Schedule-A", "Schedule-B",
        # AOS-specific
        "SCHEDULE \"A\" PROPERTY", "SCHEDULE \"B\" PROPERTY",
        "Schedule A Property", "Schedule B Property",
        "SCHEDULE OF THE FLAT HEREBY SOLD",
        "Schedule of the Flat Hereby Sold",
        "SCHEDULE OF THE PROPERTY",
        "the Schedule", "Schedule Property",
    ],

    # ─── BOUNDARIES ───────────────────────────────────────────────────────────
    "boundaries_north": [
        "North", "North Boundary", "Bounded on North",
        "Northern Boundary", "N", "NORTH",
        "North Side", "North Direction",
        "As Per Deed (North)", "As Per Actuals (North)",
        "Uttar", "Uttari Seema", "Nroth", "Norht",
        "NORTH :", "NORTH:", "North :",
        # AOS-specific
        "Gayam Motor Works Pvt Ltd",  # the value, often parsed with key
        "Corridor.",  # flat north boundary value
    ],

    "boundaries_south": [
        "South", "South Boundary", "Bounded on South",
        "Southern Boundary", "S", "SOUTH",
        "South Side", "South Direction",
        "As Per Deed (South)", "As Per Actuals (South)",
        "Dakshin", "Dakshini Seema", "Soth", "Souht",
        "SOUTH :", "SOUTH:", "South :",
        # AOS-specific
        "Limitless Synergy Pvt Ltd",  # south boundary value
        "Open To Sky.",  # flat south boundary value
    ],

    "boundaries_east": [
        "East", "East Boundary", "Bounded on East",
        "Eastern Boundary", "E", "EAST",
        "East Side", "East Direction",
        "As Per Deed (East)", "As Per Actuals (East)",
        "Purv", "Purvi Seema", "Esst", "Eatst",
        "EAST :", "EAST:", "East :",
        # AOS-specific
        "30 Feet Wide Road",  # east boundary value (open plot)
        "Corridor & Staircase",  # east boundary value (flat)
    ],

    "boundaries_west": [
        "West", "West Boundary", "Bounded on West",
        "Western Boundary", "W", "WEST",
        "West Side", "West Direction",
        "As Per Deed (West)", "As Per Actuals (West)",
        "Paschim", "Pashchimi Seema", "Wets", "Weest",
        "WEST :", "WEST:", "West :",
        # AOS-specific
        "Sy No. 83 & 84", "Sy No 83 & 84",  # west boundary value
        "Duct & Lift",  # flat west boundary value
    ],

    "north_boundary": [
        "North", "North Boundary", "Northern Boundary",
        "N. Boundary", "Bounded North", "North Side",
        "North:", "NORTH:", "Uttar Seema",
        "NORTH : ", "NORTH :",
    ],

    "south_boundary": [
        "South", "South Boundary", "Southern Boundary",
        "S. Boundary", "Bounded South", "South Side",
        "South:", "SOUTH:", "Dakshin Seema",
        "SOUTH : ", "SOUTH :",
    ],

    "east_boundary": [
        "East", "East Boundary", "Eastern Boundary",
        "E. Boundary", "Bounded East", "East Side",
        "East:", "EAST:", "Purv Seema",
        "EAST : ", "EAST :",
    ],

    "west_boundary": [
        "West", "West Boundary", "Western Boundary",
        "W. Boundary", "Bounded West", "West Side",
        "West:", "WEST:", "Paschim Seema",
        "WEST : ", "WEST :",
    ],

    "boundaries_as_per_deed": [
        "As Per Deed", "As Per Sale Deed", "As Per Document",
        "Document Boundaries", "Deed Boundaries",
        "As Per Records", "As Per Title",
        "and bounded as follows", "bounded as follows:",
        "bounded as follows:-", "and bounded as follows:",
    ],

    "boundaries_as_per_actuals": [
        "As Per Actuals", "Actual Boundaries", "Physical Boundaries",
        "On Ground", "As Measured", "As Per Site",
        "As Per Inspection", "Physical Verification",
        "As per Actual", "As per actual measurement",
    ],

    # ─── DATES ────────────────────────────────────────────────────────────────
    "agreement_date": [
        "Agreement Date", "Date of Agreement", "Date of Execution",
        "Execution Date", "Date of This Agreement",
        "Agreement Dated", "Date:", "Dated:",
        "Made on", "Executed on", "Entered into on",
        # AOS-specific
        "made and executed on this", "executed on",
        "on this 17th day of Feb 2026",
        "on this", "Date: 17-02-2026", "Date: 17/02/2026",
        "FEB-17-2026", "17-02-2026", "17/02/2026",
        "Agreement dated:", "Agreement dated",
    ],

    "inspection_date": [
        "Date of Inspection", "Inspection Date", "Date of Site Visit",
        "Site Visit Date", "Date of Survey", "Survey Date",
        "Date of Physical Verification", "Visited On",
        "Inspection Dt", "Dt of Inspection",
        "Date of Field Visit", "Visited Date",
        "Nirikshan Tithi", "Date of Inspection:",
        "Dat of Inspection", "Date Of Inspecton",
    ],

    "valuation_date": [
        "Date of Valuation", "Valuation Date", "Date of Report",
        "Report Date", "As on Date", "Valued On",
        "Dt of Valuation", "Valuation Dt",
        "Date of Assessment", "Assessment Date",
        "Mulyankan Tithi", "Date of Valuation:",
        "Date of Valuaton", "Dat of Valuation",
    ],

    "registration_date": [
        "Registration Date", "Date of Registration",
        "Registered On", "Reg Date", "Date of Reg",
        "Date Registered", "Doc Date",
        # AOS-specific
        "dated", "Dated:", "Dated :", "dated 14-03-2023",
        "dated: 14.03.2023", "registered at", "Registered at",
    ],

    "sale_deed_date": [
        "Sale Deed Date", "Date of Sale Deed",
        "Date of Purchase", "Purchase Date",
        "Date of Acquisition", "Acquired On",
        # AOS-specific
        "vide document no.", "vide document no",
        "dated 14-03-2023", "dated: 14.03.2023",
    ],

    "possession_date": [
        "Date of Possession", "Possession Date",
        "Handover Date", "Date of Handover",
        "Date of Delivery", "Delivery Date",
        # AOS-specific
        "within 1 to 6 months", "within 1 to 6 months of",
        "handed over within", "Flat will be handed over",
    ],

    "work_order_date": [
        "Work Order Date", "Date of Work Order",
        "WO Date", "Work Order Dated",
        "Work Order Agreement Date",
        "made and executed on 17/02/2026",
        "in terms of Work Order dated",
        "Work Order dated:", "WO dated",
    ],

    # ─── AREAS ────────────────────────────────────────────────────────────────
    "built_up_area": [
        "Built Up Area", "Built-Up Area", "Builtup Area",
        "BUA", "Build Up Area", "Built Area",
        "Plinth Area", "Floor Area", "Carpet Area",
        "Super Built Up Area", "Super BUA", "Covered Area",
        "Total Built Up Area", "Total BUA",
        "Construction Area", "Constructed Area",
        "sq ft", "sq. ft", "sq feet", "sqft",
        "Sq Feet", "Sq.Ft", "Square Feet",
        "Nirman Kshetrafal", "Nirman Area",
        "Bult Up Area", "Buit Up Area", "Bulit Up Area",
        # AOS-specific
        "admeasuring 1130 sq. feet", "1130 sq. feet",
        "admeasuring", "sq. feet of built up area",
        "built up area (including common areas, balconies)",
        "including common areas, balconies",
        "sq feet of built up area",
        "admeasuring 1130", "1130 sq ft",
    ],

    "land_area": [
        "Land Area", "Plot Area", "Site Area",
        "Total Land Area", "Extent of Land",
        "Land Extent", "Total Extent", "Admeasuring",
        "Measuring Area", "Land Admeasuring",
        "Plot Size", "Site Size", "Land Size",
        "Total Area", "Open Plot Area",
        "sq yards", "sq. yards", "sqyards",
        "Sq Yards", "Square Yards",
        "sq mtrs", "sq. mtrs", "sqmtrs",
        "Sq Meters", "Square Meters",
        "Acres", "Guntas", "Cents",
        "Bhumi Kshetrafal", "Zameen Ka Rukba",
        "Lnd Area", "Lad Area",
        # AOS-specific
        "790 sq. yards", "790 Square yards",
        "admeasuring area 790 sq. yards",
        "660.44 Sq Mtrs", "660.44 Sq. Mtrs",
        "total extent of admeasuring 790",
        "out of total extent of admeasuring",
        "total extent", "Extent",
    ],

    "undivided_share_of_land": [
        "Undivided Share of Land", "UDS", "UDS of Land",
        "Undivided Share", "UDS Area", "Land UDS",
        "Share of Land", "Proportionate Share",
        "Proportionate Land Share", "Common Land Share",
        "Apairth Bhoomi Hissa", "UDS in Sq Yards",
        "UDS in Sq Mtrs",
        # AOS-specific
        "undivided share of land admeasuring",
        "undivided share of land admeasuring 42.61 sq. yards",
        "42.61 sq. yards", "42.61 sq yards",
        "equivalent to 35.627 Sq. meters",
        "35.627 Sq. meters", "35.627 Sq Mtrs",
        "undivided share of land",
        "along with an undivided share of land",
    ],

    "carpet_area": [
        "Carpet Area", "Net Floor Area", "Net Area",
        "Usable Area", "Living Area",
        "Galicha Kshetrafal",
    ],

    "plinth_area": [
        "Plinth Area", "PA", "Ground Coverage",
        "Footprint Area", "Floor Plate",
    ],

    "super_built_up_area": [
        "Super Built Up Area", "Super BUA", "SBUA",
        "Gross Area", "Total Floor Area",
        "Including Common Areas", "Including Common Areas and Balconies",
        # AOS-specific
        "including common areas, balconies",
        "sq. feet of built up area (including common areas, balconies)",
    ],

    "parking": [
        "Parking", "Car Parking", "No of Parking",
        "Parking Space", "Covered Parking",
        "Open Parking", "Stilt Parking",
        "One Car Parking", "Two Car Parking",
        "Parking Slots", "Garage",
        # AOS-specific
        "One Car Parking", "1 Car Parking",
        "and One Car Parking",
        "Stilt / Parking", "Stilt Parking",
    ],

    # ─── FINANCIAL ────────────────────────────────────────────────────────────
    "total_sale_consideration": [
        "Total Sale Consideration", "Sale Consideration",
        "Total Consideration", "Sale Price",
        "Total Sale Price", "Purchase Price",
        "Total Purchase Price", "Agreement Value",
        "Contract Value", "Deal Amount",
        "Total Amount", "Property Value",
        "Vikray Mulya", "Keemat",
        "Ttal Sale Consideration", "Sale Consiedration",
        # AOS-specific
        "total sale consideration of Rs.",
        "Rs. 28,25,000/-", "28,25,000/-",
        "Rupees Twenty-Eight Lakh Twenty-Five Only",
        "Rs.28,25,000/-",
        "total sale consideration",
        "for a total sale consideration of",
    ],

    "advance_amount": [
        "Advance Amount", "Advance", "Token Amount",
        "Booking Amount", "Earnest Money",
        "Earnest Money Deposit", "EMD",
        "Initial Payment", "Upfront Payment",
        "Advance Payment", "Part Payment",
        "Advance Paid", "Amount Paid",
        "Peshgi", "Bayana", "Advance Sum",
        # AOS-specific
        "Rs. 2,82,500/-", "2,82,500/-",
        "Rupees Two Lakh Eighty-Two Thousand Five Hundred",
        "advance by way of online Transfer",
        "paid a sum of", "sum of Rs.",
        "Towards advance", "towards advance",
        "advance as part sale consideration",
    ],

    "balance_amount": [
        "Balance Amount", "Balance Sale Consideration",
        "Remaining Amount", "Balance Payment",
        "Balance Due", "Outstanding Amount",
        "Remaining Balance", "Balance to be Paid",
        "Due Amount", "Pending Amount",
        "Shesh Rakam", "Baaki Rakam",
        # AOS-specific
        "Rs. 25,42,500/-", "25,42,500/-",
        "Rupees Twenty-Five Lakh Forty-Two Thousand Five Hundred Only",
        "remaining balance of Rs.",
        "balance sale consideration",
        "subjected to Loan", "will be subjected to Loan",
    ],

    "loan_amount": [
        "Loan Amount", "Loan", "Mortgage Amount",
        "Home Loan Amount", "Finance Amount",
        "Bank Loan", "Term Loan", "Housing Loan",
        "Credit Amount", "Financed Amount",
        "HL Amount", "Loan Sanctioned",
        "Rin Rakam", "Karz",
        # AOS-specific
        "loan amount from FI/Bank",
        "The loan amount from FI/Bank",
        "Loan", "subjected to Loan",
        "loan will be directly released",
        "balance amount in favor of",
    ],

    "market_value": [
        "Market Value", "Fair Market Value", "FMV",
        "Current Market Value", "Present Market Value",
        "Market Rate", "Market Price",
        "Realizable Value", "Prevailing Market Value",
        "Value as per Market", "Open Market Value",
        "Estimated Market Value", "MV",
        "Bazaar Mulya", "Bajar Mulya",
        "Mkt Value", "Markt Value",
    ],

    "distress_value": [
        "Distress Value", "Forced Sale Value", "FSV",
        "Liquidation Value", "Auction Value",
        "Forced Liquidation Value", "FLV",
        "Minimum Realizable Value",
        "Vikray Mulya (Vivastha)", "FSV Value",
        "Distress Val", "Distres Value",
    ],

    "guideline_value": [
        "Guideline Value", "Government Value", "Govt Value",
        "Ready Reckoner Rate", "Circle Rate",
        "Stamp Duty Value", "Registration Value",
        "Sub-Registrar Value", "SRO Value",
        "Collector's Rate", "Guidance Value",
        "Basic Value", "Standard Value",
        "DC Rate", "Collector Rate",
        "Sarkari Mulya", "Sarkaari Dar",
        "Guidline Value", "Guideline Val",
    ],

    "work_order_value": [
        "Work Order Value", "Work Order Amount",
        "Total Work Value", "Contract Amount",
        "Construction Cost", "Work Value",
        "Total", "Total Amount",
        "TOTAL", "Total Value",
        # AOS/WO-specific
        "Rs. 28,25,000/-", "28,25,000/-",
        "Rupees Twenty-Eight Lakh Twenty-Five Thousand Only",
        "above works to the tune of Rs.",
        "tune of Rs.", "VALUE", "Item Value",
        "3,00,000", "3,50,000",  # individual work order line values
    ],

    "stamp_duty_value": [
        "Stamp Duty Value", "Stamp Duty",
        "Stamp Duty Paid", "Registration Charges",
        "Stamp Duty & Registration", "SD Value",
        # AOS-specific (stamp paper)
        "₹ 0000200/-", "0000200/-",
        "ZERO ZERO ZERO ZERO TWO ZERO ZERO",
        "Stamp Paper Value", "Non-Judicial Stamp",
        "India Non Judicial", "STATE BANK OF INDIA",
    ],

    # ─── LEGAL / DOCUMENT DETAILS ─────────────────────────────────────────────
    "document_no": [
        "Document No", "Document Number", "Doc No",
        "Doc. No", "Doc Number", "Registration No",
        "Registration Number", "Reg No", "Reg. No",
        "Deed No", "Sale Deed No", "Agreement No",
        "Document Bearing No", "Document No.",
        "Dastavez Sankhya",
        # AOS-specific
        "document bearing No.7085 of 2024",
        "document bearing No.8610 of 2023",
        "No. 8610 of 2023", "No. 7085 of 2024",
        "document no. 8610-2023", "vide document no.",
        "document bearing No", "document no",
        "File No.", "File No",
        "3816242", "48/2023",
    ],

    "book_no": [
        "Book No", "Book Number", "Book-I", "Book 1",
        "Book-II", "Book 2", "Book No.",
        "Register Book", "Volume No",
        # AOS-specific
        "Book-1", "Book-I", "Book 1",
        "Book-1, and Dated:", "Book-I,",
    ],

    "registered_at": [
        "Registered At", "Registered At RO",
        "Registration Office", "Sub Registrar Office",
        "SRO", "Registrar Office", "R.O.",
        "Office of Sub-Registrar", "Panjiyan Karyalay",
        # AOS-specific
        "registered at R.O Sangareddy",
        "registered at RO Sanga Reddy",
        "registered at RO Sangareddy",
        "R.O Sangareddy", "R.O. Sangareddy",
        "RO Sangareddy", "Sanga Reddy R.O.",
    ],

    "sale_deed_no": [
        "Sale Deed No", "Sale Deed Number", "Deed No",
        "Deed Number", "Sale Deed Document No",
        "Document No of Sale Deed",
        "Vikray Patra Sankhya",
        # AOS-specific
        "8610 of 2023", "No. 8610 of 2023",
        "vide document bearing No. 8610 of 2023",
        "Sale Deed vide document no. 8610-2023",
        "registered Sale Deed vide document no.",
    ],

    "development_agreement": [
        "Development Agreement", "DA",
        "Development Agreement cum GPA",
        "Joint Development Agreement", "JDA",
        "Development Agreement No", "DA No",
        # AOS-specific
        "Development Agreement cum General Power of Attorney",
        "DA cum GPA", "vide registered Development Agreement",
        "document bearing No.7085 of 2024",
        "7085 of 2024", "DA-GPA",
        "Development Agreement cum General Power of Attorney document bearing No.",
    ],

    "building_permission": [
        "Building Permission", "Building Plan Approval",
        "Construction Permission", "BP No",
        "Building Permit No", "Plan No",
        "Permit No", "Permission No",
        "File No", "GHMC File No",
        "BP File No", "Permit Number",
        # AOS-specific
        "File No. 012383/GHMC/6103/SLP2/2023-BP",
        "012383/GHMC/6103/SLP2/2023-BP",
        "permit No. 5741/GHMC/SLP/2024-BP",
        "5741/GHMC/SLP/2024-BP",
        "dt. 04-03-2024",
        "building permission from the Greater Hyderabad Municipal Corporation",
        "obtained building permission",
        "GHMC building permission",
    ],

    "layout_approval": [
        "Layout Approval", "Approved Layout",
        "Layout Plan Approval", "LP No",
        "Layout Permission", "Planning Permission",
        "Date of Issue and Validity of Layout of Approved Map / Plan",
        "Approved Map / Plan",
        "Layout Approval No", "Approved Plan",
        "mutually agreed plan", "as per the mutually agreed plan",
    ],

    "layout_approving_authority": [
        "Approved Map / Plan Issuing Authority",
        "Layout Issuing Authority",
        "Plan Sanctioning Authority",
        "Sanctioned By", "Approved By",
        "GHMC", "HMDA", "DTCP", "BDA", "CMDA",
        "Municipality", "Gram Panchayat",
        "Planning Authority", "Development Authority",
        # AOS-specific
        "Greater Hyderabad Municipal Corporation",
        "GHMC Ramachandrapuram",
        "obtained construction permission from GHMC Ramachandrapuram",
    ],

    "mortgage_details": [
        "Mortgage Details", "Mortgage", "Mortgage Information",
        "Encumbrance Details", "Encumbrances",
        "Charge Details", "Lien Details",
        "Hypothecation Details", "Pledge Details",
        "Mortgage Status", "Existing Mortgage",
        "Bandhan Vivaran", "Bhaar Vivaran",
        "Mortgge Details", "Mortgage Detials",
        # AOS-specific
        "not subject to any attachments",
        "not done anything whereby the said property may be subject to",
        "litigations, mortgages, tenancy claims",
        "dues or lien of any court",
        "legal embargo", "legal impediment",
        "Nil Encumbrance", "free from encumbrance",
    ],

    "legal_opinion": [
        "Legal Opinion", "Legal Report", "Advocate Opinion",
        "Lawyer Opinion", "Title Opinion", "Title Certificate",
        "Title Report", "Legal Clearance", "Legal Status",
        "Legal Scrutiny", "Legal Verification",
        "Advocate's Opinion", "Title Search Report",
        "Legal Opinion Certificate", "Vidhik Raay",
        "Legl Opinion", "Legel Opinion",
        # AOS-specific
        "not entered into any prior agreement for sale",
        "no agreement of sale at present",
        "neither any legal embargo",
        "no legal impediment",
        "title to the said property",
        "perfect title",
    ],

    "encumbrance_certificate": [
        "Encumbrance Certificate", "EC",
        "Encumbrance Certificate Details",
        "EC Details", "EC Period",
        "Nil Encumbrance", "Clear EC",
        "Bhaar Praman Patra",
    ],

    "patta_details": [
        "Patta Details", "Patta No", "Patta Number",
        "Patta", "Revenue Record", "Pahani",
        "Adangal", "RoR", "Record of Rights",
        "Land Records", "Revenue Extract",
    ],

    "prohibited_properties_details": [
        "Prohibited Properties Details", "Prohibited Property",
        "Prohibited Details", "Schedule Tribe Land",
        "Agency Area", "Inam Land", "Endowment Land",
        "Government Land", "Wakf Land", "Forest Land",
        "CRZ Area", "Notified Area", "Embargo",
        "Prohibited Transaction", "Transfer Prohibition",
        # AOS-specific
        "Schedule of Property is not subject matter of any kind of prohibition",
        "not subject matter of any kind of prohibition",
        "prohibition of Transfer of properties",
        "Act 9 of 1977", "prohibition",
    ],

    # ─── PROPERTY CHARACTERISTICS ─────────────────────────────────────────────
    "property_type": [
        "Property Type", "Type of Property", "Nature of Property",
        "Asset Type", "Property Category",
        "Residential", "Commercial", "Industrial",
        "Agricultural", "Mixed Use", "Open Plot",
        "Flat", "Apartment", "House", "Villa",
        "Independent House", "Row House", "Bungalow",
        "Shop", "Office", "Warehouse", "Factory",
        "Sampatti Ka Prakar",
        "Prperty Type", "Properrty Type",
        # AOS-specific
        "Semi-Finished Flat", "Residential Apartment",
        "Residential Complex", "Open Land",
        "Open Plot in Municipal Premises",
    ],

    "occupancy_status": [
        "Occupancy Status", "Occupation Status",
        "Occupancy", "Occupied By", "Occupied Status",
        "Possession Status", "Tenant Status",
        "Self Occupied", "Rented", "Vacant",
        "Owner Occupied", "Tenant Occupied",
        "Status of Occupancy", "Use Status",
        "Adhikaar Sthiti", "Qabza Sthiti",
        "Occupncy Status", "Ocupancy Status",
        # AOS-specific
        "vacant and peaceful physical possession",
        "peaceful physical possession",
        "Possession", "Semi-Finished",
    ],

    "age_of_property": [
        "Age of Property", "Age of Building",
        "Age of Structure", "Age of Construction",
        "Year of Construction", "Year Built",
        "Construction Year", "Built Year",
        "Age (Years)", "Building Age",
        "Remaining Life", "Expected Life",
        "Useful Life", "Life of Building",
        "Sampatti Ki Aayu", "Bhavan Ki Aayu",
        "Age of Proprty", "Age Of Buildng",
    ],

    "construction_type": [
        "Construction Type", "Type of Construction",
        "Structure Type", "Building Type",
        "RCC", "Load Bearing", "Steel Structure",
        "Framed Structure", "Composite",
        "Kutcha", "Pucca", "Semi-Pucca",
        "Construction Quality", "Quality of Construction",
        "Nirman Prakar",
        # AOS-specific
        "Residential Apartment Stilt / Parking + Upper 5 Floors",
        "construction of residential Apartment",
        "for constructing Residential Complex",
    ],

    "no_of_floors": [
        "No of Floors", "Number of Floors",
        "Total Floors", "No. of Floors",
        "G+", "Stilt + Upper Floors",
        "Floors", "No of Storeys",
        "Number of Storeys", "Total Storeys",
        # AOS-specific
        "Stilt / Parking + Upper 5 Floors",
        "Upper 5 Floors", "5 Floors",
        "G+5", "Stilt+5", "5th Floor",
    ],

    "road_width": [
        "Road Width", "Width of Road", "Road Facing",
        "Road Access", "Approach Road",
        "Road Size", "Road Frontage",
        "Feet Wide Road", "Meter Wide Road",
        "30 Feet Wide Road", "40 Feet Wide Road",
        # AOS-specific
        "30 Feet Wide Road",  # east boundary value
        "30 Feet Wide", "30ft Road",
    ],

    # ─── VALUATION SPECIFICS ──────────────────────────────────────────────────
    "purpose_of_valuation": [
        "Purpose for which the valuation is made",
        "Purpose of Valuation", "Purpose",
        "Reason for Valuation", "Valuation Purpose",
        "Object of Valuation", "Valuation For",
        "Loan Purpose", "Mortgage Purpose",
        "Mulyankan Ka Uddeshya",
        "Purpse of Valuation", "Purpose of Valuaton",
        # AOS/WO-specific
        "Home Loan", "Housing Loan",
        "Bank Loan Purpose", "SBI Loan",
    ],

    "list_of_documents": [
        "List of Documents", "Documents Produced",
        "Documents Submitted", "List of Documents Produced for Perusal",
        "Documents Verified", "Documents for Perusal",
        "Title Documents", "Property Documents",
        "Supporting Documents", "Documents Furnished",
        "Dastavej Soochi",
        # AOS-specific
        "requisite documents", "all the requisite documents",
        "requisite formalities and certificates",
    ],

    "rate_per_sqft": [
        "Rate per Sq Ft", "Rate / Sq Ft",
        "Rate Per Square Feet", "Per Sqft Rate",
        "Market Rate per Sqft", "Prevailing Rate",
        "Rate", "Unit Rate",
        "Dar Pratishath Varg Feet",
    ],

    "rate_per_sqyard": [
        "Rate per Sq Yard", "Rate / Sq Yard",
        "Rate Per Square Yard", "Per Sqyard Rate",
        "Land Rate", "Plot Rate",
        "Rate per Sqyd",
    ],

    # ─── WORK ORDER SPECIFICS ─────────────────────────────────────────────────
    "item_description": [
        "Item", "Item Description", "Work Item",
        "Description of Work", "Particulars",
        "Nature of Work", "Scope of Work",
        "ITEM", "Work Description",
        # WO-specific
        "S.No. ITEM VALUE", "Sl.No", "ITEM",
        "item wise", "item-wise",
    ],

    "item_value": [
        "Value", "Amount", "Cost",
        "Item Value", "Item Cost", "Work Cost",
        "Rate", "Total Value", "VALUE",
        "Item Amount",
        # WO-specific
        "3,00,000", "3,50,000", "2,50,000",
        "1,50,000", "2,25,000", "1,00,000",
        "2,00,000",
    ],

    "serial_no": [
        "S.No.", "S.No", "Sr. No", "Serial No",
        "Serial Number", "Sl No", "Sl. No",
        "No.", "No", "Item No", "S No",
        # WO-specific
        "S.No. (table column)", "1", "2", "3",
    ],

    "flooring": [
        "Flooring", "Floor Work", "Floor Finishing",
        "Tiles", "Marble", "Granite Flooring",
        "Floor Type",
        "Flooring - 3,00,000",
    ],

    "wall_finishing": [
        "Internal & External Wall Finishing in Lappam",
        "Wall Finishing", "Wall Plastering",
        "Internal Finishing", "External Finishing",
        "Lappam Finishing", "Wall Work",
        "Internal & External Wall Finishing",
        "Lappam", "Wall Finishing in Lappam",
    ],

    "painting": [
        "Painting", "Paint Work", "Interior Painting",
        "Exterior Painting", "Paint",
        "Painting - 3,50,000",
    ],

    "doors_windows": [
        "Doors/windows Shutters in Best Teak Wood",
        "Doors and Windows", "Doors / Windows",
        "Door Work", "Window Work", "Shutters",
        "Teak Wood Doors",
        "Doors/windows Shutters",
        "Best Teak Wood Doors",
    ],

    "kitchen_shelves": [
        "Kitchen and Bed Rooms Selves",
        "Kitchen Shelves", "Bedroom Shelves",
        "Shelves", "Cupboards", "Wardrobes",
        "Kitchen and Bed Rooms Shelves",
        "Kitchen Selves", "Bed Rooms Selves",
    ],

    "kitchen_platform": [
        "Kitchen Platform", "Kitchen Counter",
        "Kitchen Work", "Modular Kitchen",
        "Kitchen Platform - 1,50,000",
    ],

    "pop_ceiling": [
        "POP Ceiling with light fittings",
        "POP Ceiling", "False Ceiling",
        "Ceiling Work", "Gypsum Ceiling",
        "POP Ceiling with light fittings",
        "Light Fittings", "POP with light",
    ],

    "upvc_windows": [
        "UPVC Windows and Sliding Doors",
        "UPVC Windows", "UPVC", "Sliding Doors",
        "Aluminum Windows", "Window Frames",
        "UPVC Windows and Sliding Doors - 2,25,000",
    ],

    "electrical_works": [
        "Electrical Works", "Electrical Work",
        "Wiring", "Electrical Fitting",
        "Electrical Installation", "Electrification",
        "Electrical Works - 2,50,000",
    ],

    "electrical_piping": [
        "Electrical Piping & Wring",
        "Electrical Piping & Wiring",
        "Electrical Piping", "Piping",
        "Conduit Work", "Electrical Conduit",
        "Electrical Piping & Wring - 1,00,000",
    ],

    "sanitary_fittings": [
        "Quality sanitary fittings",
        "Sanitary Fittings", "Plumbing",
        "Sanitary Work", "Plumbing Work",
        "Sanitation", "Water Fittings",
        "Quality Sanitary Fittings",
        "Sanitary - 2,00,000",
    ],

    "pooja_room": [
        "Pooja Room Area", "Pooja Room",
        "Prayer Room", "Puja Ghar",
        "Pooja Room Area - 1,00,000",
    ],

    "bathroom_fittings": [
        "Bathroom Fittings", "Bath Fittings",
        "WC Fittings", "Toilet Fittings",
        "Bathroom Accessories",
        "Bathroom Fittings - 1,00,000",
    ],

    # ─── BANK / LOAN DETAILS ─────────────────────────────────────────────────
    "bank_name": [
        "Bank Name", "Name of Bank", "Lender Name",
        "Financial Institution", "FI Name",
        "Housing Finance Company", "HFC",
        "NBFC Name", "Lending Institution",
        "Bank / FI", "State Bank of India", "SBI",
        # AOS/WO-specific
        "The Manager, State Bank of India, Hyderabad",
        "State Bank of India, Hyderabad",
        "SBI Hyderabad", "FI/Bank",
        "loan amount from FI/Bank",
        "To The Manager, State Bank of India",
    ],

    "branch_name": [
        "Branch Name", "Branch", "Bank Branch",
        "Branch Office", "Branch Location",
        "Branch Code",
        # AOS/WO-specific
        "State Bank of India, Hyderabad",
        "Hyderabad Branch",
    ],

    "loan_account_no": [
        "Loan Account No", "Loan No",
        "Account Number", "Loan Account Number",
        "Reference No", "File No",
        "Application No", "Case No",
    ],

    "valuer_name": [
        "Valuer Name", "Name of Valuer",
        "Empanelled Valuer", "Registered Valuer",
        "Approved Valuer", "Panel Valuer",
        "Valuation Officer", "Valuer",
    ],

    "report_no": [
        "Report No", "Report Number", "Valuation Report No",
        "Reference No", "File Reference",
        "Case Reference", "Job No",
    ],

    # ─── LOCATION ─────────────────────────────────────────────────────────────
    "state": [
        "State", "State Name", "Province",
        "Telangana", "Andhra Pradesh", "Karnataka",
        "Rajya", "Prantheeya",
        "Telangana State", "T.S.",
        "Telangana State.", "TS",
    ],

    "pin_code": [
        "PIN Code", "Pin Code", "Postal Code",
        "ZIP Code", "PIN", "Pincode",
        "Area Code", "Postal PIN",
        # AOS-specific
        "500089", "502305", "502319", "507209",
    ],

    "locality": [
        "Locality", "Area", "Neighborhood",
        "Colony", "Nagar", "Extension",
        "Layout", "Sector", "Phase",
        "Mohalla", "Basti",
        # AOS-specific
        "Goutham Nagar Colony", "Narsingi",
        "Puppalaguda", "Bandlaguda",
        "BANDLAGUDA", "Bhanoor Village",
        "Chinna Korukondi", "Kokapet Road",
        "Srikirshna Goshala",
    ],

    "landmark": [
        "Landmark", "Near", "Opposite to",
        "Adjacent to", "Nearby Landmark",
        # AOS-specific
        "Srikirshna Goshala", "Kokapet Road",
        "7Hills (Pws)",
    ],

    # ─── RECEIPT / PAYMENT ───────────────────────────────────────────────────
    "receipt_no": [
        "Receipt No", "Receipt Number",
        "Payment Receipt", "Challan No",
        "Transaction ID", "Transaction Reference",
        "UTR No", "IMPS Ref No",
        "RECEIPT", "Receipt",
    ],

    "payment_mode": [
        "Payment Mode", "Mode of Payment",
        "By Online Transfer", "NEFT", "RTGS",
        "IMPS", "Cheque", "Cash", "DD",
        "Online Transfer", "Net Banking",
        # AOS-specific
        "by way of online Transfer",
        "by way of Online",
        "online transfer", "Online Transfer",
        "by way of online",
    ],

    "receipt_amount": [
        "Receipt Amount", "Amount Received",
        "Received Amount", "Amount Acknowledged",
        "Sum Received", "Received a sum of",
        # AOS-specific
        "Received a sum of Rs. 2,82,500/-",
        "Rs. 2,82,500/-", "2,82,500/-",
        "Two Lakh Eighty-Two Thousand Five Hundred",
    ],

    # ─── NOC / AGREEMENT TYPES ───────────────────────────────────────────────
    "no_objection_certificate": [
        "No Objection Certificate", "NOC",
        "No Objection", "NOC Letter",
        "No Objection Letter", "Clearance Letter",
        "Clearance Certificate", "Anaapatty Praman Patra",
        # AOS-specific (page 6)
        "No objection to getting the additional works",
        "We have no objection",
        "no objection to getting",
        "no objection to releasing the balance amount",
        "SUBJ: No objection",
        "Subject: No objection",
    ],

    "agreement_of_sale": [
        "Agreement of Sale", "AOS", "Sale Agreement",
        "Agreement for Sale", "Sale Contract",
        "Purchase Agreement",
        # AOS-specific
        "AGREEMENT OF SALE", "Agreement of Sale",
        "THIS AGREEMENT OF SALE",
        "Agreement for Sale Witnesseth",
        "NOW THIS AGREEMENT FOR SALE WITNESSETH AS UNDER",
    ],

    "work_order": [
        "Work Order", "WO", "Work Order Agreement",
        "Construction Agreement", "Contractor Agreement",
        "Work Contract",
        # WO-specific
        "WORK - ORDER", "WORK ORDER",
        "This Work Order Agreement",
        "Work Order Agreement is made and executed",
        "Work Order dated",
    ],

    "title_flow": [
        "Title Flow", "Chain of Title",
        "Title History", "Ownership History",
        "Title Documents Chain", "Title Verification",
        "Title flow to be Verified",
        # AOS-specific
        "having purchased the same under registered Sale Deed",
        "purchased the same under registered Sale Deed",
        "vide document no. 8610-2023",
        "Title to the said property",
    ],

    # ─── ADDITIONAL AOS/WO FIELDS ─────────────────────────────────────────────
    "company_registration": [
        "Company Registration", "Registered under the Company's Act",
        "Company's Act 1956", "Act 1956",
        "Registered Office", "Registration No (Company)",
        "CIN", "Corporate ID",
        "a company registered under the company's act 1956",
        "company registered under",
        "Registered Office at",
    ],

    "authorized_representative": [
        "Authorised Signatory", "Authorized Signatory",
        "Rep. by its Manager", "Manager",
        "Representative", "Authorized Representative",
        "For Limitless Synergy Pvt. Ltd",
        "For M/s LIMITLESS SYNERGY PVT LTD",
        "Sig. of the First Party", "Sig. of the Second Party",
        "SIG. OF THE FIRST PARTY",
        "SIG. OF THE SECOND PARTY(IES)",
    ],

    "stamp_paper_details": [
        "Stamp Paper No", "Stamp Paper Details",
        "Non-Judicial Stamp", "India Non Judicial",
        "STATE BANK OF INDIA", "RACPC",
        "Phone No:", "Sold To/Issued To:",
        "For Whom/ID Proof:", "Agreement",
        "Stamp Paper", "Non Judicial Stamp Paper",
        "Stamp Value", "Franking",
        "FEB-17-2026", "13+04:41",
        "3816242177133348",  # barcode number
        "48/2023",
    ],

    "party_role": [
        "First Party", "Second Party", "FIRST PARTY", "SECOND PARTY",
        "VENDOR", "VENDEE", "DEVELOPER",
        "First Party / Land Owner / Vendor",
        "FIRST PARTY / LAND OWNER / VENDOR",
        "Second Party(ies)/Contractor(s)",
        "SECOND PARTY(IES)/CONTRACTOR(S)",
    ],

    "third_party_contractor": [
        "Third Party Contractor", "Third-Party Contractor",
        "Third Party", "Contractor",
        "Third Party Contractors",
        "additional works through third-party contractors",
        "getting the additional work done by the third-party contractors",
        "separate agreements with third-party contractors",
        "additional work by entering separate agreements",
    ],

    "additional_work": [
        "Additional Work", "Additional Works",
        "Additional Work Order", "Finishing Works",
        "Balance Work", "Pending Work",
        "getting the additional works",
        "additional works through third-party contractors",
        "additional work by entering separate agreements",
    ],

    "covenants": [
        "Covenants", "Covenant", "Undertakings",
        "Conditions", "Terms and Conditions",
        "Terms", "Conditions of Sale",
        "NOW THIS AGREEMENT FOR SALE WITNESSETH AS UNDER",
        "Witnesseth", "WITNESSETH",
        "Agrees and Undertakes",
        "covenant, agrees and undertakes",
    ],

    "signatory_name": [
        "Signature", "Sign", "Signed by",
        "VENDOR (signature)", "VENDEE (signature)",
        "Sig. of First Party", "Sig. of Second Party",
        "For Limitless Synergy Pvt. Ltd",
        "Authorised Signatory",
        "V E N D O R", "V E N D E E",
        "VENDOR.", "VENDEE.",
    ],

    "remarks": [
        "Remarks", "Notes", "Observations",
        "Comments", "Additional Remarks",
        "Special Remarks", "Valuer Remarks",
        "Inspector Remarks", "General Remarks",
        "Tippani", "Aalochna",
        # AOS-specific
        "it is agreed by the both the parties",
        "agreed by both the parties",
        "and it is agreed",
    ],

    # ─── ADDITIONAL FIELDS (100+ target) ─────────────────────────────────────

    "total_plot_extent": [
        "Total Extent", "Total Plot Extent", "Total Site Extent",
        "Total Open Plot Area", "Total Land Extent",
        "out of total extent of admeasuring 790 Square yards",
        "Total Extent of Plot", "Total extent admeasuring",
        "Total extent of admeasuring", "790 Square yards",
        "admeasuring area 790",
    ],

    "property_classification": [
        "Classification of the Area", "Area Classification",
        "Locality Type", "Area Type",
        "High / Middle / Poor", "Income Category",
        "Urban / Semi Urban / Rural",
        "Class of Locality", "Locality Class",
        "Shetra Ka Vargikaran",
        "Residential Area", "Commercial Area",
        "Municipality Limits", "GHMC Limits",
        "Coming under Municipality Limits",
    ],

    "project_type": [
        "Type of Project", "Project Type",
        "Residential Complex", "Residential Apartment",
        "Commercial Complex", "Mixed Use Building",
        "constructing Residential Complex",
        "construction of residential Apartment",
        "by Name", "Named as",
    ],

    "no_of_units": [
        "No of Units", "Number of Units",
        "No of Flats", "Number of Flats",
        "No of Apartments", "Number of Apartments",
        "Total Flats", "Total Units",
    ],

    "electricity": [
        "Electricity", "Power Supply",
        "Electrical Connection", "Power Connection",
        "EB Connection", "TSECPDCL",
        "Electrical Works", "Electrification",
    ],

    "water_supply": [
        "Water Supply", "Water Connection",
        "Water Availability", "Water Source",
        "GHMC Water", "Bore Well", "Corporation Water",
        "Water Fittings", "Sanitary Fittings",
    ],

    "drainage": [
        "Drainage", "Sewage", "Drainage System",
        "UGD", "Underground Drainage",
        "Storm Water Drain",
    ],

    "amenities": [
        "Amenities", "Facilities", "Features",
        "Infrastructure", "Utilities",
        "Civic Amenities",
    ],

    "approach_road": [
        "Approach Road", "Road Access", "Road Type",
        "Road Connectivity", "Access Road",
        "Metalled Road", "Tar Road", "CC Road",
        "BT Road", "Kutcha Road",
        "30 Feet Wide Road", "30ft Road",
    ],

    "gps_coordinates": [
        "GPS Coordinates", "Geo Coordinates",
        "Lat/Long", "Latitude/Longitude",
        "GPS Location", "Coordinates",
        "Latitude", "Longitude", "Lat", "Long",
    ],

    "insurance_value": [
        "Insurance Value", "Insurable Value",
        "Insurance Amount", "Cover Amount",
        "Bima Mulya",
    ],

    "rental_value": [
        "Rental Value", "Monthly Rent",
        "Annual Rent", "Rental Income",
        "Expected Rent", "Fair Rental Value",
        "Kiraya Mulya",
    ],

    "depreciation": [
        "Depreciation", "Depreciation %",
        "Depreciation Percentage", "Dep %",
        "Accumulated Depreciation", "Wear and Tear",
        "Mulya Hras",
    ],

    "replacement_cost": [
        "Replacement Cost", "Cost of Reconstruction",
        "Reproduction Cost", "Reinstatement Cost",
        "Construction Cost", "Cost of Construction",
        "Building Cost",
    ],

    "land_value": [
        "Land Value", "Value of Land", "Plot Value",
        "Site Value", "Land Cost",
        "Bhoomi Mulya", "Zameen Mulya",
    ],

    "building_value": [
        "Building Value", "Value of Building",
        "Structure Value", "Construction Value",
        "Bhavan Mulya", "Nirman Mulya",
    ],

    "total_valuation": [
        "Total Valuation", "Total Value",
        "Total Market Value", "Gross Value",
        "Final Valuation", "Grand Total Value",
        "Kul Mulyankan", "Kul Mulya",
        "TOTAL", "Total Amount",
        "28,25,000/-",
    ],

    "genuineness_of_plan": [
        "Whether genuineness or authenticity of approved map / Plan is Verified",
        "Genuineness of Plan", "Authenticity of Plan",
        "Plan Verified", "Map Verified",
        "Approved Plan Verification", "Plan Authenticity",
    ],

    "government_enactments": [
        "Whether covered under any State / Central Govt. enactments",
        "Government Enactments", "Legal Restrictions",
        "Urban Land Ceiling", "ULC Act",
        "Agency Area", "Scheduled Area",
        "Cantonment Area", "Notified Area",
        "Government Notifications",
        "Act 9 of 1977", "prohibition of Transfer",
    ],

    "ftl_buffer_zone": [
        "FTL and Buffer Zone Details", "FTL Details",
        "Buffer Zone", "FTL Buffer Zone",
        "Full Tank Level", "Tank Bed Land",
        "Lake Buffer Zone", "Water Body Buffer",
        "Cheruvu Seema", "Lake FTL", "Water Tank",
        "FTL & Buffer Zone", "FTL / Buffer Zone",
    ],

    "photograph_reference": [
        "Photo Reference", "Photograph",
        "Site Photo", "Property Photo",
        "Photo No", "Image No",
    ],

    "site_description": [
        "Site Description", "Description of Site",
        "Site Details", "Plot Description",
        "Site Particulars", "Location Description",
    ],

    "recommendations": [
        "Recommendations", "Recommendation",
        "Suggested Value", "Recommended Value",
        "Valuer Recommendation",
    ],

    "revenue_division": [
        "Revenue Division", "Division", "Sub-Division",
        "Revenue Circle", "Circle",
        "Ramachandrapuram", "GHMC Ramachandrapuram",
    ],

    "name_of_applicant": [
        "Name of Applicant", "Applicant", "Applicant Name",
        "Customer Name", "Client Name", "Borrower",
        "Borrower Name", "Co-borrower",
        "Name of the Borrower", "Co-Applicant",
    ],

    "valuer_registration_no": [
        "Valuer Registration No", "Regd Valuer No",
        "Registration No of Valuer", "IOBB No",
        "Valuer Licence No", "Regd No",
    ],

    "locality_classification": [
        "Classification of the Area", "Area Classification",
        "Locality Type", "Area Type",
        "High / Middle / Poor", "Income Category",
        "Urban / Semi Urban / Rural",
        "Class of Locality", "Locality Class",
    ],

    "urban_rural": [
        "Urban / Semi Urban / Rural", "Urban",
        "Semi Urban", "Rural", "Area Type",
        "Location Type", "Shahari / Gramin",
        "Municipality Limits", "Gram Panchayat",
    ],

    "municipality_limits": [
        "Coming under Municipality Limits",
        "Municipality Limits", "Corporation Limits",
        "Village Panchayat", "Panchayat Area",
        "GHMC Limits", "Municipal Corporation",
        "Gram Panchayat Limits", "Nagar Palika",
        "ULB Limits",
        "under GHMC", "GHMC Ramachandrapuram",
    ],

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
        req = getattr(self, "required_fields", None)
        if req is not None and field_key not in req:
            return create_scored_field(None)
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
        req = getattr(self, "required_fields", None)
        if req is not None and field_key not in req:
            return create_scored_field(None)
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
