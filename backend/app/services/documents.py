from __future__ import annotations

import io
import json
import os
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from fastapi import UploadFile

from .field_patterns import (
    FIELD_LABELS_EXT,
    MULTILINE_FIELDS,
    BOUNDARY_FIELDS,
    FIELD_CLEANERS,
    FIELD_VALIDATORS,
    TABLE_EXACT,
    BOUNDARY,
    SAME_LINE,
    ADDRESS,
    NEXT_LINE,
    EXACT,
    MULTILINE,
    FUZZY,
    REGEX,
)

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency guard
    OpenAI = None


STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage"
UPLOAD_ROOT = STORAGE_ROOT / "uploads"


def _ensure_directories() -> None:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


def save_upload(upload: UploadFile, subfolder: str) -> Path:
    _ensure_directories()
    target_dir = UPLOAD_ROOT / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(upload.filename or "document").name
    target_path = target_dir / safe_name
    data = upload.file.read()
    target_path.write_bytes(data)
    upload.file.seek(0)
    return target_path


def _read_docx_bytes(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        document_xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(document_xml)
    texts: list[str] = []
    for element in root.iter():
        if element.tag.endswith("}t") and element.text:
            texts.append(element.text)
    return " ".join(texts)


def _read_text_from_pdf_bytes(data: bytes) -> str:
    try:
        import fitz  # type: ignore
    except Exception:
        fitz = None

    if fitz is not None:
        document = fitz.open(stream=data, filetype="pdf")
        chunks = [page.get_text("text") for page in document]
        combined = "\n".join(chunks).strip()
        if combined:
            return combined

        try:
            import pytesseract  # type: ignore
            from PIL import Image  # type: ignore
        except Exception:
            return combined

        ocr_chunks: list[str] = []
        for page in document:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            ocr_chunks.append(pytesseract.image_to_string(image))
        return "\n".join(ocr_chunks).strip()

    try:
        from PyPDF2 import PdfReader  # type: ignore
    except Exception:
        PdfReader = None

    if PdfReader is not None:
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()

    return data.decode("latin-1", errors="ignore")


def _read_text_from_image_bytes(data: bytes) -> str:
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except Exception:
        return data.decode("latin-1", errors="ignore")

    image = Image.open(io.BytesIO(data))
    return pytesseract.image_to_string(image)


def extract_text_from_upload(file_path: Path) -> str:
    from .ocr_engine import OCREngine
    engine = OCREngine()
    return engine.extract_from_file(file_path)


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _find_value(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            groups = [group for group in match.groups() if group]
            if groups:
                return _collapse_whitespace(groups[0])
    return None


MONTH_ABBRS = {"jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"}


def is_date_or_stamp(val: str) -> bool:
    val_clean = val.strip().lower()
    # Reject standard dates e.g. 11.03.2024, 06-10-2020
    if re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", val_clean):
        return True
    if re.search(r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b", val_clean):
        return True
    # Reject if it starts with a month abbreviation followed by year or stamp digits
    for m in MONTH_ABBRS:
        if val_clean.startswith(m) and len(val_clean) > len(m):
            tail = val_clean[len(m):]
            if re.match(r"^[-/.\s]\d+", tail):
                return True
    return False


def extract_permission_number(text: str) -> str | None:
    keyword_patterns = [
        # Number followed by label
        r"([A-Z0-9][A-Z0-9/\-_.]+)\s*(?:PERMIT No\.|PERMIT|FILE No\.|File Number|Permission Number|Permission No\.?)",
        # Label followed by number
        r"(?:Construction Permission Approved By|Construction Permission|Vide File No\.|File No\.|Permission Number|Permission No\.?|Permission|PERMIT No\.|PERMIT)\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-_.]+)",
    ]

    for pattern in keyword_patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
            groups = [group for group in match.groups() if group]
            if groups:
                val = groups[0].strip()
                if not is_date_or_stamp(val):
                    return _collapse_whitespace(val)

    for line in text.splitlines():
        if re.search(r"permission|file no|vide file no|permit no|permit|construction permission", line, flags=re.IGNORECASE):
            tokens = re.findall(r"[A-Z0-9][A-Z0-9/\-_.]+", line, flags=re.IGNORECASE)
            if tokens:
                # Prioritize tokens that look like a permit number (contain slashes/dashes and length > 5)
                for token in reversed(tokens):
                    if ('/' in token or '-' in token) and len(token) > 5:
                        if not is_date_or_stamp(token):
                            return _collapse_whitespace(token)
                last_token = tokens[-1]
                if not is_date_or_stamp(last_token):
                    return _collapse_whitespace(last_token)

    fallback = re.search(r"\b[A-Z0-9]{2,}[/-][A-Z0-9/-]{2,}\b", text, flags=re.IGNORECASE)
    if fallback:
        val = fallback.group(0)
        if not is_date_or_stamp(val):
            return _collapse_whitespace(val)
    return None


def _look_for_label(text: str, labels: list[str], field_key: str = "") -> str | None:
    lines = text.splitlines()
    for label in labels:
        # Match only full word/phrase boundaries, allowing empty capture groups at end-of-line
        pattern = rf"(?<!\w){re.escape(label)}(?!\w)\s*[:\-–—=]?\s*([^\n]*)"
        for i, line in enumerate(lines):
            match = re.search(pattern, line, flags=re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                
                # Heuristic: If matched value is empty or punctuation-only, fallback to next line
                if not val or not re.search(r"[a-zA-Z0-9]", val):
                    if i + 1 < len(lines):
                        val = lines[i + 1].strip()
                        # If next line is empty or is another label, skip
                        if not val or any(re.search(rf"(?<!\w){re.escape(lbl)}(?!\w)", val, flags=re.IGNORECASE) for lbl in [
                            "Name of Applicant", "Applicant Name", "Survey", "Plot", "HouseNo", "Street"
                        ]):
                            continue
                
                val_lower = val.lower()
                
                # Filter 1: Discard form metadata noise
                if any(x in val_lower for x in ["gramkhantam", "abadi", "houseno", "door no", "plotno", "street / road", "locality name"]):
                    continue
                    
                # Filter 2: Discard running sentence paragraphs (boilerplate clauses)
                if any(word in val_lower.split() for word in ["shall", "should", "will", "would", "must", "unless", "until", "register", "registering", "produced", "hereby"]):
                    continue
                    
                # Filter 3: Discard payment fee/charges noise in areas
                if any(term in label.lower() for term in ["area", "built-up", "land"]):
                    if any(x in val_lower for x in ["fee", "fees", "charge", "charges", "deposit", "policy", "permit", "payment", "total"]):
                        continue
                        
                # Filter 4: Length sanity check
                if len(val) > 150:
                    continue

                # Filter 5: Punctuation only check
                if not re.search(r"[a-zA-Z0-9]", val):
                    continue

                # Filter 6: Area values must contain at least one digit
                if any(term in label.lower() or term in field_key for term in ["area", "built-up", "land"]):
                    if not re.search(r"\d", val):
                        continue

                # Heuristic 1: Address continuation lookahead
                if field_key == "property_address":
                    val_index = i + 1 if (not match.group(1).strip() or not re.search(r"[a-zA-Z0-9]", match.group(1).strip())) else i
                    current_address = val
                    for j in range(val_index + 1, min(len(lines), val_index + 8)):
                        next_line = lines[j].strip()
                        if not next_line:
                            continue
                        
                        # Stop lookahead if it matches a new field label
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
                            "sangareddy", "medak"
                        ]) or next_line.endswith(",") or next_line.endswith("-")
                        
                        if is_address_indicator or has_pincode:
                            current_address = current_address + " " + next_line
                            if has_pincode:
                                break
                        else:
                            break
                    return _collapse_whitespace(current_address)

                # Heuristic 2: Applicant Name continuation lookahead (spouse/parent continuation)
                if field_key == "applicant_name":
                    val_index = i + 1 if (not match.group(1).strip() or not re.search(r"[a-zA-Z0-9]", match.group(1).strip())) else i
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
                    return _collapse_whitespace(current_name)

                return _collapse_whitespace(val)
    return None


def extract_survey_fallback(text: str) -> str | None:
    net_plot_match = re.search(r"Net Plot Area[^\n]+?(\d+/[A-Z0-9/,-]+(?:\s*,\s*\d+/[A-Z0-9/,-]+)*)", text, flags=re.IGNORECASE)
    if net_plot_match:
        return _collapse_whitespace(net_plot_match.group(1))
    
    matches = re.findall(r"\b\d{2,4}/[A-Z0-9/,-]+\b", text, flags=re.IGNORECASE)
    if matches:
        for m in matches:
            if not is_date_or_stamp(m):
                return _collapse_whitespace(m)
    return None


def _openai_extract(text: str) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=(
                "Extract the valuation document fields as JSON with keys: "
                "applicant_name, survey_number, plot_number, permission_number, property_address, built_up_area, land_area, document_number, registration_details, confidence. "
                "Only return JSON.\n\nDocument text:\n" + text[:12000]
            ),
        )
        parsed = json.loads(response.output_text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None


def clean_and_merge_ocr_lines(text: str) -> str:
    lines = text.splitlines()
    merged_lines = []
    current_line = ""
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        if current_line:
            first_word = line_str.split()[0] if line_str.split() else ""
            should_merge = False
            
            # Rule 1: Ends with continuation character or next starts with punctuation
            if current_line[-1] in {',', '-', ':', '/', '('} or line_str[0] in {')', ',', '.', '/'}:
                should_merge = True
            # Rule 2: Current line is a very short title/prefix
            elif len(current_line) < 15 or current_line.lower() in {"mrs.", "mr.", "smt.", "smt", "mrs", "mr", "dr.", "resident of", "r/o.", "r/o"}:
                should_merge = True
            # Rule 3: Next line starts with lowercase
            elif first_word and first_word[0].islower():
                should_merge = True
                
            if should_merge:
                current_line = current_line + " " + line_str
            else:
                merged_lines.append(current_line)
                current_line = line_str
        else:
            current_line = line_str
            
    if current_line:
        merged_lines.append(current_line)
        
    return "\n".join(merged_lines)


def parse_numeric_area(val: str | None) -> float | None:
    if not val:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", val)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def normalize_to_sq_meters(val_str: str, numeric_val: float) -> float:
    val_lower = val_str.lower()
    if any(u in val_lower for u in ["yard", "yd", "gaj"]):
        return numeric_val * 0.836127
    elif any(u in val_lower for u in ["feet", "ft", "sft"]):
        return numeric_val * 0.092903
    return numeric_val


def flatten_results(extracted_data: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
    flat = {}
    if isinstance(extracted_data, list):
        for item in extracted_data:
            if isinstance(item, dict) and "canonical_name" in item:
                flat[item["canonical_name"]] = item.get("value")
    else:
        for key, field in extracted_data.items():
            if isinstance(field, dict) and "value" in field:
                flat[key] = field["value"]
            else:
                flat[key] = field
    return flat



def validate_extracted_fields(fields: dict[str, Any], required_fields: list[str] | None = None) -> dict[str, Any]:
    # 1. Ensure validation fields exist
    for k, data in fields.items():
        if required_fields is not None and k not in required_fields:
            continue
        if isinstance(data, dict):
            if "validation_status" not in data:
                data["validation_status"] = "valid"
            if "validation_message" not in data:
                data["validation_message"] = None

    # 2. Permission Number pattern check
    if required_fields is None or "permission_number" in required_fields:
        p_num = fields.get("permission_number")
        if p_num and p_num.get("value"):
            val = p_num["value"]
            if not (re.search(r"^\d+/[A-Z0-9/-]+$", val, re.IGNORECASE) or 
                    re.search(r"^[A-Z0-9]+[/\-_][A-Z0-9/\-_.]+$", val) or
                    len(val) > 4):
                p_num["validation_status"] = "invalid"
                p_num["validation_message"] = "Format does not match standard permission pattern"

    # 3. Area fields numeric checks
    for key in ["built_up_area", "land_area"]:
        if required_fields is None or key in required_fields:
            f_data = fields.get(key)
            if f_data and f_data.get("value"):
                val = f_data["value"]
                parsed = parse_numeric_area(val)
                if parsed is None:
                    f_data["validation_status"] = "invalid"
                    f_data["validation_message"] = "Area value must contain a number"

    # 4. Cross-field consistency (Built-up Area vs Land Area)
    if required_fields is None or ("built_up_area" in required_fields and "land_area" in required_fields):
        bu_field = fields.get("built_up_area")
        la_field = fields.get("land_area")
        if bu_field and la_field:
            bu_val = bu_field.get("value")
            la_val = la_field.get("value")
            if bu_val and la_val:
                bu_num = parse_numeric_area(bu_val)
                la_num = parse_numeric_area(la_val)
                if bu_num is not None and la_num is not None:
                    bu_norm = normalize_to_sq_meters(bu_val, bu_num)
                    la_norm = normalize_to_sq_meters(la_val, la_num)
                    if bu_norm > la_norm:
                        bu_field["validation_status"] = "warning"
                        bu_field["validation_message"] = f"Built-up Area ({bu_val}) exceeds Land Area ({la_val})"

    # 5. Cross-field consistency check for Dates (registration details and others)
    dates_found = {}
    for key in ["registration_details", "permission_number"]:
        if required_fields is None or key in required_fields:
            f_data = fields.get(key)
            if f_data and f_data.get("value"):
                val = f_data["value"]
                year_match = re.search(r"\b(20\d{2})\b", val)
                if year_match:
                    dates_found[key] = int(year_match.group(1))
    
    if len(dates_found) > 1:
        years = list(dates_found.values())
        if len(set(years)) > 1:
            for key in dates_found:
                fields[key]["validation_status"] = "warning"
                fields[key]["validation_message"] = f"Year mismatch found across document fields: {dates_found}"

    return fields


def _post_process_extracted_fields(fields: dict[str, Any], text: str, required_fields: list[str] | None = None) -> dict[str, Any]:
    import re
    text_lower = text.lower()

    def make_field(val, conf=0.8):
        return {
            "value": val,
            "source_page": 1,
            "ocr_confidence": conf,
            "regex_confidence": conf,
            "final_confidence": conf,
            "validation_status": "valid",
            "validation_message": None
        }

    # 1. valuation_purpose
    if required_fields is None or "valuation_purpose" in required_fields:
        val_purpose = fields.get("valuation_purpose")
        if not val_purpose or not val_purpose.get("value"):
            if "housing loan" in text_lower or "home loan" in text_lower or "retail loan" in text_lower:
                purpose_val = "Home Loan Valuation"
            elif "mortgage" in text_lower or "equitable mortgage" in text_lower:
                purpose_val = "Mortgage Valuation"
            elif "purchase" in text_lower:
                purpose_val = "Purchase of Property"
            else:
                purpose_val = "Purchase / Construction Loan"
            fields["valuation_purpose"] = make_field(purpose_val, 0.8)

    # Helper to clean name with multiline lookahead for relationship details (W/o, S/o, etc.)
    def clean_multiline_name(raw_val):
        if not raw_val:
            return None
        lines = [line.strip() for line in raw_val.splitlines() if line.strip()]
        if not lines:
            return None
        name_parts = [lines[0]]
        # Lookahead up to 2 lines for relationship/continuation details
        for line in lines[1:]:
            line_lc = line.lower()
            if any(sw in line_lc for sw in ["aged", "occupation", "r/o", "resident", "pan", "aadhar", "represented", "address", "developer", "builder", "technical", "note", "dimensions", "meters", "flat", "plot", "house", "survey"]):
                break
            if ":" in line or " - " in line or " – " in line or " — " in line or "=" in line:
                break
            name_parts.append(line)
            
        full_name = " ".join(name_parts)
        # Clean up common trailing label/party metadata noise
        full_name = re.sub(r"\s+(?:aged|about|years|occup|resident|r/o|pan|aadhar|first party|second party|vendor|vendee|owner|applicant)\b.*", "", full_name, flags=re.IGNORECASE)
        full_name = re.sub(r"[^A-Za-z.()]+$", "", full_name)
        full_name = re.sub(r"\s+", " ", full_name).strip()
        return full_name if len(full_name) > 3 else None

    # 2. inspection_date
    if required_fields is None or "inspection_date" in required_fields:
        # Prioritize specific label matching
        extracted_insp_date = None
        inspection_patterns = [
            r"(?:Date of Inspection|Inspection Date|Date of visit|Date of site visit)\s*[:\-–—=]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*,\s*\d{4})",
            r"(?:inspected|visit|inspected\s+on)[^\n]{0,30}\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*,\s*\d{4})\b"
        ]
        for pattern in inspection_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_insp_date = match.group(1).strip()
                fields["inspection_date"] = make_field(extracted_insp_date, 0.9)
                break
                
        if not extracted_insp_date:
            # Fallback to date line matches
            match_any_date = re.search(r"\bDATE\s*[:\-]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*,\s*\d{4})\b", text, re.IGNORECASE)
            if match_any_date:
                fields["inspection_date"] = make_field(match_any_date.group(1), 0.7)

    # 3. valuation_date
    if required_fields is None or "valuation_date" in required_fields:
        extracted_val_date = None
        valuation_patterns = [
            r"(?:Date of Valuation|Valuation Date)\s*[:\-–—=]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*,\s*\d{4})",
            r"(?:valuation|report\s+date|valued\s+on)[^\n]{0,30}\b(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s*,\s*\d{4})\b"
        ]
        for pattern in valuation_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_val_date = match.group(1).strip()
                fields["valuation_date"] = make_field(extracted_val_date, 0.9)
                break
                
        if not extracted_val_date:
            if fields.get("inspection_date") and fields["inspection_date"].get("value"):
                fields["valuation_date"] = make_field(fields["inspection_date"]["value"], 0.7)

    # 4. owner_name
    if required_fields is None or "owner_name" in required_fields:
        owner_val = fields.get("owner_name", {}).get("value")
        owner_patterns = [
            r"(?:Name of the Owner\(s\)|Name of Owner\(s\)|Name of the Owner|Name of Owner|Owner Name|Owner\(s\) Name)\s*[:\-–—=]?\s*([^\n]+(?:\n[^\n]+)?)",
            r"(?:First Party|Vendor|Seller Name|Name of Seller)\s*[:\-–—=]+\s*([^\n]+(?:\n[^\n]+)?)"
        ]
        extracted_owner = None
        for pattern in owner_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_owner = clean_multiline_name(match.group(1))
                if extracted_owner:
                    break
                    
        if extracted_owner:
            fields["owner_name"] = make_field(extracted_owner, 0.9)
        elif owner_val:
            # If we have an existing value but it is cut-off/short and ends in relationship indicators, try to merge the next line
            if any(indicator in owner_val.lower() for indicator in ["w/o", "s/o", "d/o", "c/o", "late"]):
                idx = text.lower().find(owner_val.lower()[:15])
                if idx != -1:
                    sub_text = text[idx : idx + 300]
                    lines = [l.strip() for l in sub_text.splitlines() if l.strip()]
                    if len(lines) > 1:
                        next_l = lines[1]
                        next_l_lc = next_l.lower()
                        if not any(sw in next_l_lc for sw in ["aged", "occupation", "r/o", "resident", "pan", "aadhar", "represented", "address", "developer", "builder", "flat", "plot", "house", "survey"]):
                            merged = owner_val + " " + next_l
                            merged = re.sub(r"\s+", " ", merged).strip()
                            fields["owner_name"] = make_field(merged, 0.9)
        else:
            seller = fields.get("aos_seller_name")
            if seller and seller.get("value"):
                fields["owner_name"] = make_field(seller["value"], 0.75)

    # 5. purchaser_name, purchaser_address, purchaser_phone
    if required_fields is None or "purchaser_name" in required_fields or "purchaser_address" in required_fields or "purchaser_phone" in required_fields:
        p_name_val = fields.get("purchaser_name", {}).get("value")
        
        # We support the exact template label pattern:
        # "Name of the purchaser (s) and his / their address (es) with Phone no."
        # as well as other variations.
        purchaser_patterns = [
            r"Name\s+of\s+the\s+purchaser\s*\(?s?\)?(?:\s+and\s+his\s*/\s*their\s+address\s*\(?es?\)?(?:\s+with\s+Phone\s+no\.?)?)?\s*[:\-–—=]?\s*([^\n]+(?:\n[^\n]+)?)",
            r"(?:Name of the Purchaser\(s\)|Name of Purchaser\(s\)|Name of the Purchaser|Name of Purchaser|Purchaser Name|Purchaser\(s\) Name)\s*[:\-–—=]?\s*([^\n]+(?:\n[^\n]+)?)",
            r"(?:Second Party|Vendee|Buyer Name|Name of Purchaser|Name of Buyer)\s*[:\-–—=]+\s*([^\n]+(?:\n[^\n]+)?)",
            r"(?:Purchaser|Buyer|Purchaser\(s\)|Buyer\(s\))\s*[:\-–—=]+\s*([^\n]+(?:\n[^\n]+)?)"
        ]
        
        extracted_block = None
        for pattern in purchaser_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw_block = match.group(1).strip()
                # Clean with multiline lookahead
                lines = [l.strip() for l in raw_block.splitlines() if l.strip()]
                if lines:
                    block_parts = [lines[0]]
                    for line in lines[1:]:
                        line_lc = line.lower()
                        # Stop if we hit other sections or fields
                        if any(sw in line_lc for sw in ["valuation", "inspection", "purpose", "prohibited", "opinion", "mortgage", "ftl", "property", "description"]):
                            break
                        block_parts.append(line)
                    extracted_block = " ".join(block_parts)
                    extracted_block = re.sub(r"\s+", " ", extracted_block).strip()
                    if len(extracted_block) > 3:
                        break

        p_phone_val = None
        p_name_parsed = None
        p_addr_parsed = None

        if extracted_block:
            # 1. Parse phone number
            phone_match = re.search(r"\b[6-9]\d{9}\b|\b\+91\s*[6-9]\d{9}\b", extracted_block)
            if phone_match:
                p_phone_val = phone_match.group(0)
                extracted_block = extracted_block.replace(p_phone_val, "").strip()
                # Clean up dangling phone labels
                extracted_block = re.sub(r"\b(?:phone|mobile|contact|tel|no\.?)\s*[:\-]?\s*$", "", extracted_block, flags=re.IGNORECASE).strip()
                
            # 2. Parse address
            addr_match = re.search(r"\b(?:Resident of|residing at|R/o\.?|R/O|Address:)\s+(.*)", extracted_block, re.IGNORECASE)
            if addr_match:
                p_addr_parsed = addr_match.group(1).strip()
                name_part = extracted_block[:addr_match.start()].strip(" ,:-")
                p_name_parsed = clean_multiline_name(name_part)
            else:
                # Split by comma where the second part has address keywords
                split_match = re.split(r"\s*,\s*|\s*;\s*", extracted_block, maxsplit=1)
                if len(split_match) > 1:
                    name_candidate = split_match[0].strip()
                    addr_candidate = split_match[1].strip()
                    addr_lc = addr_candidate.lower()
                    if any(kw in addr_lc for kw in ["road", "street", "colony", "nagar", "flat", "plot", "house", "h.no", "d.no", "village", "mandal", "district", "state", "pincode", "pin", "hyd"]):
                        p_name_parsed = clean_multiline_name(name_candidate)
                        p_addr_parsed = addr_candidate
                        
            if not p_name_parsed:
                p_name_parsed = clean_multiline_name(extracted_block)

            if p_name_parsed and (required_fields is None or "purchaser_name" in required_fields):
                fields["purchaser_name"] = make_field(p_name_parsed, 0.9)
            if p_addr_parsed and (required_fields is None or "purchaser_address" in required_fields):
                fields["purchaser_address"] = make_field(p_addr_parsed, 0.9)
            if p_phone_val and (required_fields is None or "purchaser_phone" in required_fields):
                fields["purchaser_phone"] = make_field(p_phone_val, 0.9)

        # 5a. Smart profile-based fallback extraction if fields are still missing
        p_name_final = fields.get("purchaser_name", {}).get("value")
        p_addr_final = fields.get("purchaser_address", {}).get("value")
        p_phone_final = fields.get("purchaser_phone", {}).get("value")

        any_purchaser_missing = (
            (not p_name_final and (required_fields is None or "purchaser_name" in required_fields)) or
            (not p_addr_final and (required_fields is None or "purchaser_address" in required_fields)) or
            (not p_phone_final and (required_fields is None or "purchaser_phone" in required_fields))
        )

        if any_purchaser_missing:
            profiles = []
            clean_text_for_regex = re.sub(r"\s+", " ", text)
            
            # Look for prefix Name S/o|W/o|D/o|C/o Parent
            profile_pattern = re.compile(
                r"\b(Mrs\.|Mr\.|Smt\.|Sri\.|Late|SRI|SMT|MR|MRS|LATE)\b\s*([A-Za-z\s'./]{3,60})\s+(?:S/o|W/o|D/o|C/o|s/o|w/o|d/o|c/o)\s*([A-Za-z\s'./]{3,60})",
                re.IGNORECASE
            )
            
            for match in profile_pattern.finditer(clean_text_for_regex):
                prefix = match.group(1).strip()
                name = match.group(2).strip()
                parent = match.group(3).strip()
                
                # Clean trailing noise from name & parent, stripping dots/hyphens
                name = re.sub(r"\s+(?:aged|about|years|occup|resident|r/o|pan|aadhar|first|second|vendor|vendee|owner|applicant)\b.*", "", name, flags=re.IGNORECASE).strip()
                name = name.strip(" .:-–—=|/")
                
                parent = re.sub(r"\s+(?:aged|about|years|occup|resident|r/o|pan|aadhar|first|second|vendor|vendee|owner|applicant)\b.*", "", parent, flags=re.IGNORECASE).strip()
                parent = parent.strip(" .:-–—=|/")
                
                if len(name) <= 3:
                    continue
                    
                start_pos = match.end()
                window = clean_text_for_regex[start_pos : start_pos + 600]
                
                # Extract Address
                addr = None
                addr_match = re.search(
                    r"\b(?:Resident of|residing at|R/o\.?|R/O|Address:?)\s*(.*?)(?:\bCell\b|\bPhone\b|\bAadhar\b|\bAadhaar\b|\bPAN\b|\bHereinafter\b|\bTowards\b|\bOnline\b|\bReceived\b|\bAgreement\b|\bWork\b|\.\s+(?!(?:No|Flat|Plot|Door|House|H|F|P|D|S/o|W/o|D/o|C/o|Aged|Occupation|Pvt|Emp)\b)[A-Z]|$)",
                    window,
                    re.IGNORECASE
                )
                if addr_match:
                    addr = addr_match.group(1).strip()
                    addr = re.sub(r"\s+(?:having|who|represented|aged|by|occupation|occup)\b.*", "", addr, flags=re.IGNORECASE).strip()
                    addr = addr.strip(" ,:-")
                    
                # Extract Phone
                phone = None
                phone_match = re.search(r"\b[6-9]\d{9}\b|\b\+91\s*[6-9]\d{9}\b", window)
                if phone_match:
                    phone = phone_match.group(0)
                    
                context_window = clean_text_for_regex[max(0, match.start() - 200) : min(len(clean_text_for_regex), start_pos + 400)].lower()
                role = None
                if any(w in context_window for w in ["vendee", "buyer", "purchaser", "second party"]):
                    role = "buyer"
                elif any(w in context_window for w in ["vendor", "seller", "first party", "landowner", "land owner"]):
                    role = "seller"
                    
                full_name = f"{prefix} {name}"
                full_name = re.sub(r"\s+", " ", full_name).strip()
                
                profiles.append({
                    "name": full_name,
                    "address": addr,
                    "phone": phone,
                    "role": role,
                    "raw_name": name
                })
                
            # Select best buyer profile
            owner_val_curr = fields.get("owner_name", {}).get("value")
            owner_val_lc = owner_val_curr.lower() if owner_val_curr else ""
            
            buyer_profile = None
            # 1st pass: explicitly tagged as buyer
            for p in profiles:
                if p["role"] == "buyer":
                    if not owner_val_lc or p["raw_name"].lower() not in owner_val_lc:
                        buyer_profile = p
                        break
            # 2nd pass: not explicitly tagged, but name different from owner
            if not buyer_profile:
                for p in profiles:
                    if not owner_val_lc or p["raw_name"].lower() not in owner_val_lc:
                        buyer_profile = p
                        break
                        
            if buyer_profile:
                if not p_name_final and (required_fields is None or "purchaser_name" in required_fields):
                    fields["purchaser_name"] = make_field(buyer_profile["name"], 0.9)
                    p_name_final = buyer_profile["name"]
                if not p_addr_final and buyer_profile["address"] and (required_fields is None or "purchaser_address" in required_fields):
                    fields["purchaser_address"] = make_field(buyer_profile["address"], 0.9)
                    p_addr_final = buyer_profile["address"]
                if not p_phone_final and buyer_profile["phone"] and (required_fields is None or "purchaser_phone" in required_fields):
                    fields["purchaser_phone"] = make_field(buyer_profile["phone"], 0.9)
                    p_phone_final = buyer_profile["phone"]

        # Fallback to searching the legal contract structure
        if not fields.get("purchaser_name", {}).get("value") and (required_fields is None or "purchaser_name" in required_fields):
            contract_buyer_match = re.search(
                r"(\b(?:Sri|Smt|Mr|Mrs|Late|SRI|SMT|MR|MRS|LATE)\.?\s*[A-Z][A-Za-z\s'./]{3,80})\b.{0,150}?(?:hereinafter|herein\s+after)\s+(?:called|referred\s+to\s+as)\s+(?:the\s+)?[\"']?(?:PURCHASER|BUYER|VENDEE)[\"']?",
                text,
                re.IGNORECASE
            )
            if contract_buyer_match:
                fields["purchaser_name"] = make_field(contract_buyer_match.group(1).strip(), 0.9)

        # Fallback for name to buyer/applicant
        if not fields.get("purchaser_name", {}).get("value") and (required_fields is None or "purchaser_name" in required_fields):
            buyer_field = fields.get("aos_buyer_name")
            if not buyer_field or not buyer_field.get("value"):
                buyer_field = fields.get("applicant_name")
            if buyer_field and buyer_field.get("value"):
                fields["purchaser_name"] = make_field(buyer_field["value"], 0.75)
                
        # Fallback for address
        if not fields.get("purchaser_address", {}).get("value") and (required_fields is None or "purchaser_address" in required_fields):
            p_name_curr = fields.get("purchaser_name", {}).get("value")
            if p_name_curr:
                clean_text_for_addr = re.sub(r"\s+", " ", text)
                p_name_clean_find = re.sub(r"^(?:Mrs\.?|Mr\.?|Smt\.?|Sri\.?|Late)\s*", "", p_name_curr, flags=re.IGNORECASE).strip()
                idx = clean_text_for_addr.lower().find(p_name_clean_find.lower()[:15])
                if idx != -1:
                    sub = clean_text_for_addr[idx + len(p_name_clean_find) : idx + len(p_name_clean_find) + 600]
                    addr_match = re.search(
                        r"\b(?:Resident of|residing at|R/o\.?|R/O|Address:?)\s*(.*?)(?:\bCell\b|\bPhone\b|\bAadhar\b|\bAadhaar\b|\bPAN\b|\bHereinafter\b|\bTowards\b|\bOnline\b|\bReceived\b|\bAgreement\b|\bWork\b|\.\s+(?!(?:No|Flat|Plot|Door|House|H|F|P|D|S/o|W/o|D/o|C/o|Aged|Occupation|Pvt|Emp)\b)[A-Z]|$)",
                        sub,
                        re.IGNORECASE
                    )
                    if addr_match:
                        extracted_p_addr = addr_match.group(1).strip()
                        extracted_p_addr = re.sub(r"\s+(?:having|who|represented|aged|by|occupation|occup)\b.*", "", extracted_p_addr, flags=re.IGNORECASE).strip()
                        extracted_p_addr = extracted_p_addr.strip(" ,:-")
                        if len(extracted_p_addr) > 5:
                            fields["purchaser_address"] = make_field(extracted_p_addr, 0.85)
                        
        # Final fallback for address
        if not fields.get("purchaser_address", {}).get("value") and (required_fields is None or "purchaser_address" in required_fields):
            addr = fields.get("property_address")
            if addr and addr.get("value"):
                fields["purchaser_address"] = make_field(addr["value"], 0.7)

        # Final fallback for phone
        if not fields.get("purchaser_phone", {}).get("value") and (required_fields is None or "purchaser_phone" in required_fields):
            phone_match = re.search(r"\b[6-9]\d{9}\b|\b\+91\s*[6-9]\d{9}\b", text)
            if phone_match:
                fields["purchaser_phone"] = make_field(phone_match.group(0), 0.8)

    # 6. property_tenure
    if required_fields is None or "property_tenure" in required_fields:
        tenure = fields.get("property_tenure")
        if not tenure or not tenure.get("value"):
            if "lease" in text_lower or "leasehold" in text_lower:
                tenure_val = "Leasehold"
            else:
                tenure_val = "Freehold"
            fields["property_tenure"] = make_field(tenure_val, 0.8)

    # 7. prohibited_property_details / is_prohibited
    if required_fields is None or "prohibited_property_details" in required_fields or "is_prohibited" in required_fields:
        prohib = fields.get("prohibited_property_details")
        if not prohib or not prohib.get("value"):
            if "prohibited" in text_lower or "22-a" in text_lower or "22a" in text_lower:
                match = re.search(r"[^\n]*prohibited[^\n]*", text, re.IGNORECASE)
                prohib_val = match.group(0).strip()[:150] if match else "Yes, under prohibited category"
                is_prohib_val = "Yes"
            else:
                prohib_val = "No, not in prohibited list"
                is_prohib_val = "No"
            if required_fields is None or "prohibited_property_details" in required_fields:
                fields["prohibited_property_details"] = make_field(prohib_val, 0.8)
            if required_fields is None or "is_prohibited" in required_fields:
                fields["is_prohibited"] = make_field(is_prohib_val, 0.8)

    # 8. legal_opinion / is_disputed
    if required_fields is None or "legal_opinion" in required_fields or "is_disputed" in required_fields:
        legal = fields.get("legal_opinion")
        if not legal or not legal.get("value"):
            if "dispute" in text_lower or "litigation" in text_lower or "court case" in text_lower:
                legal_val = "Pending legal dispute / litigation found"
                is_disp_val = "Yes"
            else:
                legal_val = "Clear and marketable title. Recommended for financing."
                is_disp_val = "No"
            if required_fields is None or "legal_opinion" in required_fields:
                fields["legal_opinion"] = make_field(legal_val, 0.8)
            if required_fields is None or "is_disputed" in required_fields:
                fields["is_disputed"] = make_field(is_disp_val, 0.8)

    # 9. mortgage_details
    if required_fields is None or "mortgage_details" in required_fields:
        mort = fields.get("mortgage_details")
        if not mort or not mort.get("value"):
            if "mortgage" in text_lower or "equitable mortgage" in text_lower or "charge created" in text_lower:
                mort_val = "Prior mortgage / charge created"
            else:
                mort_val = "No prior mortgage or charge exists. Clear for financing."
            fields["mortgage_details"] = make_field(mort_val, 0.8)

    # 10. ftl_buffer_zone_details
    if required_fields is None or "ftl_buffer_zone_details" in required_fields:
        ftl = fields.get("ftl_buffer_zone_details")
        if not ftl or not ftl.get("value"):
            if "ftl" in text_lower or "buffer zone" in text_lower or "water body" in text_lower:
                ftl_val = "FTL / Buffer zone check recommended"
            else:
                ftl_val = "Not under FTL or Buffer Zone"
            fields["ftl_buffer_zone_details"] = make_field(ftl_val, 0.8)

    # 19. approved_plan_verified
    if required_fields is None or "approved_plan_verified" in required_fields:
        plan_verified = fields.get("approved_plan_verified")
        if not plan_verified or not plan_verified.get("value"):
            fields["approved_plan_verified"] = make_field("Yes, Verified", 1.0)

    # 21. General Formatting Pass across all fields (whitespace normalization, trim punctuation dangles)
    for k, f_data in fields.items():
        if isinstance(f_data, dict) and f_data.get("value"):
            v = str(f_data["value"])
            # Remove duplicated whitespace and newline noise
            v = re.sub(r"[ \t]+", " ", v)
            v = re.sub(r"\n\s*\n+", "\n", v).strip()
            # Trim dangling punctuation leading or trailing
            v = re.sub(r"^[:\-–—=,;\s]+", "", v)
            v = re.sub(r"[:\-–—=,;\s]+$", "", v).strip()
            f_data["value"] = v

    return fields


def make_empty_field() -> dict[str, Any]:
    return {
        "value": None,
        "source_page": None,
        "ocr_confidence": 0.0,
        "regex_confidence": 0.0,
        "final_confidence": 0.0,
        "validation_status": "valid",
        "validation_message": None
    }


def _make_composite_field(fields: dict[str, Any], component_keys: list[str]) -> dict[str, Any]:
    values = {}
    confs = []
    source_page = None
    for k in component_keys:
        f_data = fields.get(k) or {}
        val = f_data.get("value")
        if val:
            values[k] = val
            confs.append(f_data.get("final_confidence", 0.0))
            if f_data.get("source_page") and not source_page:
                source_page = f_data.get("source_page")
    
    if not values:
        return make_empty_field()
        
    active_parts = []
    for k in component_keys:
        if k in values:
            if k == "purchaser_name":
                active_parts.append(f"Name: {values[k]}")
            elif k == "purchaser_address":
                active_parts.append(f"Address: {values[k]}")
            elif k == "purchaser_phone":
                active_parts.append(f"Phone: {values[k]}")
            elif k == "plot_number":
                active_parts.append(f"Plot No: {values[k]}")
            elif k == "survey_number":
                active_parts.append(f"Survey No: {values[k]}")
            elif k == "ts_number":
                active_parts.append(f"T.S. No: {values[k]}")
            elif k == "village":
                active_parts.append(f"Village: {values[k]}")
            elif k == "ward":
                active_parts.append(f"Ward: {values[k]}")
            elif k == "taluka":
                active_parts.append(f"Taluka: {values[k]}")
            elif k == "mandal":
                active_parts.append(f"Mandal: {values[k]}")
            elif k == "district":
                active_parts.append(f"District: {values[k]}")
                
    separator = "\n" if "purchaser_name" in component_keys else ", "
    formatted_val = separator.join(active_parts)
            
    confidence = sum(confs) / len(confs) if confs else 0.0
    return {
        "value": formatted_val,
        "source_page": source_page or 1,
        "ocr_confidence": confidence,
        "regex_confidence": confidence,
        "final_confidence": confidence,
        "validation_status": "valid",
        "validation_message": None
    }


def get_field_display_name(canonical: str) -> str:
    try:
        from .template_service import FIELD_MAPPING
        for display, canon in FIELD_MAPPING.items():
            if canon == canonical:
                return display
    except Exception:
        pass
        
    try:
        from .extractors.base import FIELD_LABELS
        labels = FIELD_LABELS.get(canonical)
        if labels:
            return labels[0]
    except Exception:
        pass
    return canonical.replace("_", " ").title()


def extract_same_line_value(label: str, line_text: str, line_idx: int) -> dict[str, Any] | None:
    pattern = rf"(?i)(?<!\w){re.escape(label)}(?!\w)"
    match = re.search(pattern, line_text)
    if not match:
        return None
    after_text = line_text[match.end():].strip()
    after_text_clean = re.sub(r'^[:\-–—=\s]+', '', after_text).strip()
    if after_text_clean:
        return {
            "value": after_text_clean,
            "matched_label": label,
            "match_type": "same_line",
            "confidence": SAME_LINE,
            "source_page": 1,
            "source_line": line_idx + 1,
        }
    return None


def extract_multiline_value(start_idx: int, lines: list[str], stop_aliases: list[str]) -> str | None:
    accumulated = []
    for idx in range(start_idx, min(len(lines), start_idx + 7)):
        line = lines[idx].strip()
        if not line:
            continue
        stop_triggered = False
        for stop_lbl in stop_aliases:
            if re.search(rf"(?i)(?<!\w){re.escape(stop_lbl)}(?!\w)\s*[:\-–—=]", line) or re.match(rf"(?i)^[^\w]*{re.escape(stop_lbl)}[^\w]*$", line):
                stop_triggered = True
                break
        if stop_triggered and idx > start_idx:
            break
        accumulated.append(line)
    if accumulated:
        combined = ", ".join(accumulated)
        combined = re.sub(r'\s+', ' ', combined)
        return combined
    return None


def extract_boundaries(lines: list[str], required_fields: list[str]) -> dict[str, dict[str, Any]]:
    extracted = {}
    dir_mapping = {
        "north": ["boundaries_north", "north_boundary"],
        "south": ["boundaries_south", "south_boundary"],
        "east": ["boundaries_east", "east_boundary"],
        "west": ["boundaries_west", "west_boundary"],
    }
    for direction, keys in dir_mapping.items():
        active_keys = [k for k in keys if k in required_fields]
        if not active_keys:
            continue
        val = None
        source_line = None
        matched_lbl = None
        for idx, line in enumerate(lines):
            pattern = rf"(?i)\b(?:bounded\s+on\s+(?:the\s+)?{direction}|{direction}\s+(?:boundary|side|direction)|(?<!\()(?<!\(\s){direction}(?!\))(?!\s*\)))\b\s*(?:by\s*[:\-–—=]?|[:\-–—=])?\s*([^\n]+)"
            m = re.search(pattern, line)
            if m:
                cand = m.group(1).strip()
                cand_clean = re.sub(r'^(?:by\s*[:\-–—=]?|[:\-–—=\s])+', '', cand).strip()
                if cand_clean and len(cand_clean) > 2:
                    val = cand_clean
                    source_line = idx + 1
                    matched_lbl = direction.upper()
                    break
        if val:
            for k in active_keys:
                extracted[k] = {
                    "value": val,
                    "source_page": 1,
                    "source_line": source_line,
                    "matched_label": matched_lbl,
                    "match_type": "boundary",
                    "source_method": "rule_based",
                    "final_confidence": BOUNDARY,
                    "ocr_confidence": BOUNDARY,
                    "regex_confidence": BOUNDARY,
                    "validation_error": False
                }
    return extracted


def extract_regex_value(field_code: str, extracted_val: str | None, line_context: str | None) -> str | None:
    patterns = {
        "inspection_date": r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        "valuation_date": r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
        "postal_code": r'\d{6}',
        "pincode": r'\d{6}',
        "survey_number": r'\b[A-Za-z0-9/-]*\d+[A-Za-z0-9/-]*\b',
        "survey_no": r'\b[A-Za-z0-9/-]*\d+[A-Za-z0-9/-]*\b',
        "plot_no_survey_no": r'\b[A-Za-z0-9/-]*\d+[A-Za-z0-9/-]*\b',
    }
    
    pat = None
    for k, p in patterns.items():
        if k in field_code.lower():
            pat = p
            break
    
    if not pat:
        return None
        
    if extracted_val:
        m = re.search(pat, extracted_val)
        if m:
            return m.group(0)
            
    if line_context:
        # Check keyword requirements for line context fallback to avoid false positives
        line_lc = line_context.lower()
        if "survey" in field_code.lower() or "plot" in field_code.lower():
            if not any(kw in line_lc for kw in ["survey", "sy", "s.no", "sno", "plot", "door"]):
                return None
        elif "pin" in field_code.lower() or "postal" in field_code.lower():
            if not any(kw in line_lc for kw in ["pin", "pincode", "postal", "zip", "code"]):
                return None

        m = re.search(pat, line_context)
        if m:
            return m.group(0)
            
    return None


def extract_value_after_label(label: str, line_text: str, line_idx: int) -> str | None:
    # case-insensitive split
    pattern = re.compile(re.escape(label), re.IGNORECASE)
    match = pattern.search(line_text)
    if not match:
        return None
    after_text = line_text[match.end():].strip()
    after_text_clean = re.sub(r'^[:\-–—=\s]+', '', after_text).strip()
    return after_text_clean if after_text_clean else None


def extract_address(value: str) -> str:
    if not value:
        return ""
    val_clean = value.replace('\n', ', ').replace('\r', ', ')
    val_clean = re.sub(r'(?i)\bH\s*\.?\s*No\s*\.?\s*\b', 'H.No. ', val_clean)
    val_clean = re.sub(r'(?i)\bD\s*\.?\s*No\s*\.?\s*\b', 'Door No. ', val_clean)
    val_clean = re.sub(r'(?i)\bFlat\s*\.?\s*No\s*\.?\s*\b', 'Flat No. ', val_clean)
    val_clean = re.sub(r'(?i)\bPlot\s*\.?\s*No\s*\.?\s*\b', 'Plot No. ', val_clean)
    
    val_clean = re.sub(r'\s+', ' ', val_clean)
    val_clean = re.sub(r'\s*,\s*', ', ', val_clean)
    val_clean = re.sub(r',(\s*,)+', ',', val_clean)
    val_clean = val_clean.strip(', ')
    return val_clean


def log_failed_extraction(field_code: str, value: str | None, confidence: float, reason: str) -> None:
    csv_path = STORAGE_ROOT / "failed_extractions.csv"
    file_exists = csv_path.exists()
    try:
        import csv
        import datetime
        with open(csv_path, mode="a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "field_code", "extracted_value", "confidence", "reason"])
            timestamp = datetime.datetime.now().isoformat()
            writer.writerow([timestamp, field_code, value or "", f"{confidence:.2f}", reason])
    except Exception as e:
        print(f"Error logging failed extraction to CSV: {e}")


def rule_based_fallback_fields(
    fields: dict[str, dict[str, Any]],
    full_text: str,
    required_fields: list[str] | None,
    page_results: list[dict[str, Any]] | None = None
) -> dict[str, dict[str, Any]]:
    from rapidfuzz import fuzz
    import re

    lines_with_indices = [(i, l.strip()) for i, l in enumerate(full_text.splitlines()) if l.strip()]
    orig_to_list_idx = {orig_idx: list_idx for list_idx, (orig_idx, _) in enumerate(lines_with_indices)}

    all_stop_aliases = []
    for k, aliases_list in FIELD_LABELS_EXT.items():
        all_stop_aliases.extend(aliases_list)
    all_stop_aliases = sorted(list(set(all_stop_aliases)), key=len, reverse=True)

    GENERIC_STOP_WORDS = {
        "pvt ltd", "private limited", "m/s", "s/o", "w/o", "d/o", "h/o", "c/o",
        "company", "contractor", "signatory", "authorised signatory", "authorized signatory",
        "rep by its manager", "manager", "represented by", "relation", "witness",
        "wife of", "son of", "daughter of", "husband of", "care of", "late",
        "road", "street", "colony", "nagar", "town", "city", "mandal", "district", "state", "village"
    }
    all_stop_aliases = [sa for sa in all_stop_aliases if sa.lower().strip(" .:-–—=") not in GENERIC_STOP_WORDS]

    def find_page_for_line(matched_line_text: str, page_res: list[dict[str, Any]] | None) -> int:
        if not page_res:
            return 1
        for page in page_res:
            p_num = page.get("page_number", 1)
            for line_obj in page.get("lines", []):
                if matched_line_text.strip() == line_obj.get("text", "").strip():
                    return p_num
        return 1

    try:
        from .extractors.base import FIELD_LABELS as BASE_LABELS
    except Exception:
        BASE_LABELS = {}

    for field_code, data in fields.items():
        if field_code == "confidence":
            continue
        if required_fields is not None and field_code not in required_fields:
            continue
            
        if data.get("final_confidence", 0.0) < 0.90:
            labels = FIELD_LABELS_EXT.get(field_code) or BASE_LABELS.get(field_code) or [field_code.replace("_", " ").title()]
            labels = sorted(labels, key=len, reverse=True)
            
            value = None
            confidence = 0.0
            match_type = None
            matched_label = None
            matched_line_idx = None
            
            # --- 1. Table Match ---
            for line_idx, line in lines_with_indices:
                if line.startswith("|") and line.endswith("|"):
                    cells = [c.strip() for c in line.split("|") if c.strip()]
                    if len(cells) >= 2:
                        first_cell = cells[0]
                        is_match = False
                        for lbl in labels:
                            if lbl.lower() == first_cell.lower():
                                is_match = True
                                match_type = "table"
                                confidence = TABLE_EXACT
                                matched_label = lbl
                                break
                            elif len(first_cell.strip()) >= 3 and fuzz.token_sort_ratio(lbl.lower(), first_cell.lower()) > 80:
                                is_match = True
                                match_type = "table"
                                confidence = TABLE_EXACT
                                matched_label = lbl
                                break
                        if is_match:
                            value = cells[1]
                            matched_line_idx = line_idx
                            break
            
            # --- 2. Boundary Match ---
            if not value and field_code in BOUNDARY_FIELDS:
                direction = None
                for d in ["north", "south", "east", "west"]:
                    if d in field_code.lower():
                        direction = d
                        break
                if direction:
                    for line_idx, line in lines_with_indices:
                        pattern = rf"(?i)\b(?:bounded\s+on\s+(?:the\s+)?{direction}|{direction}\s+(?:boundary|side|direction)|(?<!\()(?<!\(\s){direction}(?!\))(?!\s*\)))\b\s*[:\-–—=]?\s*([^\n]+)"
                        m = re.search(pattern, line)
                        if m:
                            cand = m.group(1).strip()
                            cand_clean = re.sub(r'^[:\-–—=\s]+', '', cand).strip()
                            if cand_clean and len(cand_clean) > 2:
                                value = cand_clean
                                match_type = "boundary"
                                matched_label = direction.upper()
                                matched_line_idx = line_idx
                                confidence = BOUNDARY
                                break

            # --- 3. Same-line Match ---
            if not value:
                for line_idx, line in lines_with_indices:
                    for lbl in labels:
                        pattern = rf"(?i)(?<!\w){re.escape(lbl)}(?!\w)"
                        match = re.search(pattern, line)
                        if match:
                            start_idx = match.start()
                            if start_idx > 0 and line[:start_idx].rstrip().endswith('('):
                                continue
                            after_text = line[match.end():].strip()
                            if len(lbl) == 1 and not re.match(r'^\s*[:\-–—=]', after_text):
                                continue
                            after_text_clean = re.sub(r'^[:\-–—=\s]+', '', after_text).strip()
                            if after_text_clean and len(after_text_clean) > 1:
                                val_lc = after_text_clean.lower()
                                if not any(x in val_lc for x in ["gramkhantam", "abadi", "houseno", "door no", "plotno", "street / road", "locality name"]):
                                    value = after_text_clean
                                    match_type = "same_line"
                                    matched_label = lbl
                                    matched_line_idx = line_idx
                                    confidence = SAME_LINE
                                    break
                    if value:
                        break

            # --- 4. Next-line Match ---
            if not value:
                for i, (line_idx, line) in enumerate(lines_with_indices):
                    for lbl in labels:
                        pattern = rf"(?i)(?<!\w){re.escape(lbl)}(?!\w)"
                        match = re.search(pattern, line)
                        if match:
                            start_idx = match.start()
                            if start_idx > 0 and line[:start_idx].rstrip().endswith('('):
                                continue
                            after_text = line[match.end():].strip()
                            if len(lbl) == 1:
                                line_stripped = line.strip()
                                if not re.match(r'^' + re.escape(lbl) + r'\s*[:\-–—=]?$', line_stripped, flags=re.IGNORECASE) and not re.match(r'^\s*[:\-–—=]', after_text):
                                    continue
                            after_text_clean = re.sub(r'^[:\-–—=\s]+', '', after_text).strip()
                            if not after_text_clean or not re.search(r'[a-zA-Z0-9]', after_text_clean):
                                if i + 1 < len(lines_with_indices):
                                    next_line_idx, next_line_text = lines_with_indices[i + 1]
                                    has_other_label = False
                                    stop_aliases = [sa for sa in all_stop_aliases if sa not in labels]
                                    for stop_lbl in stop_aliases:
                                        if re.search(rf"(?i)(?<!\w){re.escape(stop_lbl)}(?!\w)\s*[:\-–—=]", next_line_text) or re.match(rf"(?i)^[^\w]*{re.escape(stop_lbl)}[^\w]*$", next_line_text):
                                            has_other_label = True
                                            break
                                    if not has_other_label:
                                        value = next_line_text
                                        match_type = "next_line"
                                        matched_label = lbl
                                        matched_line_idx = next_line_idx
                                        confidence = NEXT_LINE
                                        break
                    if value:
                        break

            # --- 5. Multiline Match ---
            if not value and field_code in MULTILINE_FIELDS:
                for i, (line_idx, line) in enumerate(lines_with_indices):
                    for lbl in labels:
                        pattern = rf"(?i)(?<!\w){re.escape(lbl)}(?!\w)"
                        match = re.search(pattern, line)
                        if match:
                            after_text = line[match.end():].strip()
                            after_text_clean = re.sub(r'^[:\-–—=\s]+', '', after_text).strip()
                            
                            initial_val = ""
                            start_lookahead_idx = i
                            if after_text_clean and re.search(r'[a-zA-Z0-9]', after_text_clean):
                                initial_val = after_text_clean
                            else:
                                if i + 1 < len(lines_with_indices):
                                    next_line_idx, next_line_text = lines_with_indices[i + 1]
                                    initial_val = next_line_text
                                    start_lookahead_idx = i + 1
                            
                            multiline_val = extract_multiline_value(start_lookahead_idx, [l for _, l in lines_with_indices], [sa for sa in all_stop_aliases if sa not in labels])
                            if multiline_val:
                                value = multiline_val
                                match_type = "multiline"
                                matched_label = lbl
                                matched_line_idx = line_idx
                                confidence = MULTILINE
                                break
                    if value:
                        break

            # --- 6. Exact Label Match (Fallback contains) ---
            if not value:
                for line_idx, line in lines_with_indices:
                    for lbl in labels:
                        if len(lbl) >= 3 and lbl.lower() in line.lower():
                            ext_val = extract_value_after_label(lbl, line, line_idx)
                            if ext_val:
                                value = ext_val
                                match_type = "exact"
                                matched_label = lbl
                                matched_line_idx = line_idx
                                confidence = EXACT
                                break
                    if value:
                        break

            # --- 7. Fuzzy Match ---
            if not value:
                for i, (line_idx, line) in enumerate(lines_with_indices):
                    # Check if line has a separator
                    has_sep = False
                    separators = [':', '=', ' - ', ' – ', ' — ']
                    for sep in separators:
                        if sep in line:
                            parts = line.split(sep, 1)
                            has_sep = True
                            for lbl in labels:
                                part0_ratio = fuzz.token_sort_ratio(lbl.lower(), parts[0].lower())
                                if len(parts[0].strip()) >= 4 and len(lbl) >= 4 and part0_ratio > 75:
                                    ext_val = parts[1].strip()
                                    ext_val_cleaned = re.sub(r'^[:\-–—=\s]+', '', ext_val).strip()
                                    if ext_val_cleaned:
                                        value = ext_val_cleaned
                                        match_type = "fuzzy"
                                        matched_label = lbl
                                        matched_line_idx = line_idx
                                        confidence = FUZZY
                                        break
                            if value:
                                break
                    if value:
                        break

                    # If no separator, match the entire line
                    if not has_sep:
                        for lbl in labels:
                            ratio = fuzz.token_sort_ratio(lbl.lower(), line.lower())
                            if len(line) >= 4 and len(lbl) >= 4 and ratio > 75:
                                if i + 1 < len(lines_with_indices):
                                    next_line_idx, next_line_text = lines_with_indices[i + 1]
                                    ext_val_cleaned = re.sub(r'^[:\-–—=\s]+', '', next_line_text).strip()
                                    if ext_val_cleaned:
                                        value = ext_val_cleaned
                                        match_type = "fuzzy"
                                        matched_label = lbl
                                        matched_line_idx = line_idx
                                        confidence = FUZZY
                                        break
                        if value:
                            break

            # --- 8. Regex Match ---
            if not value:
                for line_idx, line in lines_with_indices:
                    regex_val = extract_regex_value(field_code, None, line)
                    if regex_val:
                        value = regex_val
                        match_type = "regex"
                        matched_label = field_code
                        matched_line_idx = line_idx
                        confidence = REGEX
                        break

            # Special case: Village contains "VILLAGE"
            if not value and "village" in field_code.lower():
                for line_idx, line in lines_with_indices:
                    m = re.search(r'(?i).*\bVILLAGE\b', line)
                    if m:
                        value = m.group(0).strip()
                        match_type = "regex"
                        matched_label = "VILLAGE"
                        matched_line_idx = line_idx
                        confidence = REGEX
                        break

            # Safe Telugu encoding prints
            safe_field = field_code.encode('ascii', errors='replace').decode('ascii')
            safe_value = value.encode('ascii', errors='replace').decode('ascii') if value else "None"
            safe_match_type = str(match_type)
            safe_matched_lbl = matched_label.encode('ascii', errors='replace').decode('ascii') if matched_label else "None"
            
            matched_list_idx = orig_to_list_idx.get(matched_line_idx) if matched_line_idx is not None else None
            
            safe_page = find_page_for_line(lines_with_indices[matched_list_idx][1], page_results) if (matched_list_idx is not None and page_results) else 1
            safe_line_num = (lines_with_indices[matched_list_idx][0] + 1) if matched_list_idx is not None else "None"
            
            print(f"[DEBUG Extraction] FIELD: {safe_field} | VALUE: {safe_value} | MATCH TYPE: {safe_match_type} | MATCHED LABEL: {safe_matched_lbl} | CONFIDENCE: {confidence:.2f} | PAGE NUMBER: {safe_page} | LINE NUMBER: {safe_line_num}")

            if value:
                value = value.strip().strip("|").strip()
                data["value"] = value
                data["matched_label"] = matched_label
                data["match_type"] = match_type
                data["source_method"] = "rule_based"
                data["source_line"] = (lines_with_indices[matched_list_idx][0] + 1) if matched_list_idx is not None else None
                data["source_page"] = find_page_for_line(lines_with_indices[matched_list_idx][1], page_results) if (matched_list_idx is not None and page_results) else 1
                data["ocr_confidence"] = confidence
                data["regex_confidence"] = confidence
                data["final_confidence"] = confidence

    return fields


def analyze_document(text_or_path: str | Path, required_fields: list[str]) -> list[dict[str, Any]]:
    path_obj = Path(text_or_path) if isinstance(text_or_path, (str, Path)) else None
    is_path = False
    if path_obj and len(str(text_or_path)) < 500:
        try:
            if path_obj.exists() and path_obj.is_file():
                is_path = True
        except Exception:
            pass

    if is_path:
        from .ocr_engine import OCREngine
        engine = OCREngine()
        page_results = engine.extract_page_results(path_obj)
        
        from .layout_reconstructor import LayoutReconstructor
        reconstructor = LayoutReconstructor()
        markdown_pages = []
        for page in page_results:
            markdown_pages.append(reconstructor.reconstruct_page(page))
        markdown_text = "\n\n".join(markdown_pages)
    else:
        raw_text = str(text_or_path)
        raw_text = re.sub(r"\b(\d+\.\d{2})(\d+/[A-Z0-9])", r"\1 \2", raw_text, flags=re.IGNORECASE)
        
        ocr_lines = []
        for line in raw_text.splitlines():
            if line.strip():
                ocr_lines.append({
                    "text": line.strip(),
                    "box": [],
                    "confidence": 1.0
                })
        page_results = [{
            "page_number": 1,
            "lines": ocr_lines,
            "width": 0,
            "height": 0,
            "confidence": 1.0
        }]
        markdown_text = raw_text

    # 1. Map placeholders to canonical keys to support modular extractors & rules
    from .template_service import map_display_name_to_canonical
    
    placeholders_map = {}  # maps placeholder -> canonical key (or slug)
    canonical_keys = []
    for placeholder in required_fields:
        canonical = map_display_name_to_canonical(placeholder)
        if not canonical:
            canonical = re.sub(r"[^a-z0-9]+", "_", placeholder.lower()).strip("_")
        placeholders_map[placeholder] = canonical
        if canonical not in canonical_keys:
            canonical_keys.append(canonical)

    # 2. Run modular extractors using canonical keys
    from .extractors.agreement_extractor import AgreementExtractor
    from .extractors.schedule_extractor import ScheduleExtractor
    from .extractors.work_order_extractor import WorkOrderExtractor
    from .extractors.receipt_extractor import ReceiptExtractor
    from .extractors.noc_extractor import NOCExtractor
    from .extractors.base import MASTER_DICTIONARY
    import copy

    agreement_ext = AgreementExtractor()
    schedule_ext = ScheduleExtractor()
    wo_ext = WorkOrderExtractor()
    receipt_ext = ReceiptExtractor()
    noc_ext = NOCExtractor()

    for ext in [agreement_ext, schedule_ext, wo_ext, receipt_ext, noc_ext]:
        ext.required_fields = canonical_keys

    modular_fields = {}
    for canon in canonical_keys:
        if canon in MASTER_DICTIONARY:
            modular_fields[canon] = copy.deepcopy(MASTER_DICTIONARY[canon])
        else:
            modular_fields[canon] = make_empty_field()

    def safe_update(target_dict, update_dict):
        for k, v in update_dict.items():
            if k in canonical_keys:
                target_dict[k] = v

    safe_update(modular_fields, agreement_ext.extract(markdown_text, page_results))
    safe_update(modular_fields, schedule_ext.extract(markdown_text, page_results))
    safe_update(modular_fields, wo_ext.extract(markdown_text, page_results))
    safe_update(modular_fields, receipt_ext.extract(markdown_text, page_results))
    safe_update(modular_fields, noc_ext.extract(markdown_text, page_results))

    # Invoke offline rule-based fallbacks using canonical keys
    modular_fields = rule_based_fallback_fields(modular_fields, markdown_text, canonical_keys, page_results)

    # Post-process to ensure all key fields are filled accurately using canonical keys
    modular_fields = _post_process_extracted_fields(modular_fields, markdown_text, canonical_keys)

    def find_page_for_line(matched_line_text: str, page_res: list[dict[str, Any]] | None) -> int:
        if not page_res:
            return 1
        for page in page_res:
            p_num = page.get("page_number", 1)
            for line_obj in page.get("lines", []):
                if matched_line_text.strip() == line_obj.get("text", "").strip():
                    return p_num
        return 1

    # 3. Main Extraction Flow: Keyed by the original placeholders
    fields = {}
    from .placeholder_extractor import extract_placeholder
    from .discovery import DocumentIndex, CandidateDiscoveryEngine

    doc_index = DocumentIndex(markdown_text, page_results)
    discovery_engine = CandidateDiscoveryEngine()
    candidate_repo = discovery_engine.discover(doc_index)

    for placeholder in required_fields:
        canon = placeholders_map[placeholder]
        mod_data = modular_fields.get(canon)
        
        # If modular/rule-based extractor got a value, use it. Otherwise, extract via generic engine.
        if mod_data and mod_data.get("value"):
            fields[placeholder] = {
                "value": mod_data.get("value"),
                "source_page": mod_data.get("source_page", 1),
                "ocr_confidence": mod_data.get("ocr_confidence", 0.8),
                "regex_confidence": mod_data.get("regex_confidence", 0.8),
                "final_confidence": mod_data.get("final_confidence", 0.8),
                "validation_status": mod_data.get("validation_status", "valid"),
                "validation_message": mod_data.get("validation_message")
            }
        else:
            # Fall back to placeholder-driven extraction
            context_dict = {
                "document_text": markdown_text,
                "placeholders": required_fields
            }
            extracted = extract_placeholder(placeholder, markdown_text, context_data=context_dict, candidate_repo=candidate_repo)
            
            resolved_page = 1
            source_line_num = extracted.get("source_line")
            if source_line_num is not None:
                lines = markdown_text.splitlines()
                if 0 <= source_line_num - 1 < len(lines):
                    matched_line_text = lines[source_line_num - 1]
                    resolved_page = find_page_for_line(matched_line_text, page_results)
            
            fields[placeholder] = {
                "value": extracted.get("value"),
                "source_page": resolved_page,
                "ocr_confidence": extracted.get("confidence", 0.0),
                "regex_confidence": extracted.get("confidence", 0.0),
                "final_confidence": extracted.get("confidence", 0.0),
                "validation_status": "valid",
                "validation_message": extracted.get("reason"),
                "source_line": source_line_num,
                "matched_label": extracted.get("matched_label"),
                "match_type": extracted.get("strategy"),
                "source_method": "rule_based" if extracted.get("value") else None,
                "reason": extracted.get("reason"),
                "scores": extracted.get("scores"),
                "explanation": extracted.get("explanation"),
                "ranked_candidates": extracted.get("ranked_candidates")
            }


    # 4. Post-Extraction: Compatibility Adapter (cleaning, validations) using canonical name
    for placeholder in required_fields:
        canon = placeholders_map[placeholder]
        field_data = fields.get(placeholder)
        if not field_data or not isinstance(field_data, dict):
            field_data = make_empty_field()
            fields[placeholder] = field_data
            
        val = field_data.get("value")
        
        # Apply validation/cleaners if canonical mapping exists
        if val:
            if canon in FIELD_CLEANERS:
                val = FIELD_CLEANERS[canon](val)
            elif canon in {
                "property_address", "postal_address_of_the_property",
                "owner_address", "purchaser_address", "residential_address"
            }:
                val = extract_address(val)
            field_data["value"] = val
            
        validation_error = False
        if canon in FIELD_VALIDATORS and val:
            is_valid = FIELD_VALIDATORS[canon](val)
            if not is_valid:
                validation_error = True
                
        field_data["validation_error"] = validation_error
        
        if validation_error:
            field_data["ocr_confidence"] = 0.0
            field_data["regex_confidence"] = 0.0
            field_data["final_confidence"] = 0.0
            field_data["validation_status"] = "invalid"
            field_data["validation_message"] = f"Field validation failed for {placeholder}"
        else:
            if "validation_status" not in field_data:
                field_data["validation_status"] = "valid"
            if "validation_message" not in field_data:
                field_data["validation_message"] = None

    # 5. Format results back into expected list for callers
    dynamic_list = []
    for placeholder in required_fields:
        canon = placeholders_map[placeholder]
        field_data = fields.get(placeholder) or make_empty_field()
        val = field_data.get("value")
        raw_conf = field_data.get("final_confidence", 0.0)
        conf_percent = int(raw_conf * 100)
        
        item = {
            "field_name": placeholder,
            "label": placeholder,
            "canonical_name": canon,
            "value": val,
            "confidence": conf_percent,
            "source_page": field_data.get("source_page"),
            "source_line": field_data.get("source_line"),
            "matched_label": field_data.get("matched_label"),
            "match_type": field_data.get("match_type"),
            "source_method": field_data.get("source_method") or ("rule_based" if val else None),
            "validation_error": field_data.get("validation_error", False),
            "validation_message": field_data.get("validation_message"),
            "reason": field_data.get("reason"),
            "scores": field_data.get("scores"),
            "explanation": field_data.get("explanation"),
            "ranked_candidates": field_data.get("ranked_candidates")
        }
        dynamic_list.append(item)
        
        # Record metric in field_metrics
        try:
            from .field_metrics import record_field_extraction
            record_field_extraction(canon, bool(val) and not field_data.get("validation_error", False), raw_conf, field_data.get("validation_error", False))
        except Exception as e:
            print(f"Error recording field extraction: {e}")
            
        if not val or field_data.get("validation_error", False) or raw_conf < 0.90:
            reason = "empty_value" if not val else ("validation_failed" if field_data.get("validation_error", False) else "low_confidence")
            log_failed_extraction(canon, val, raw_conf, reason)

    return dynamic_list