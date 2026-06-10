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


def validate_extracted_fields(fields: dict[str, Any]) -> dict[str, Any]:
    # 1. Ensure validation fields exist
    for k, data in fields.items():
        if isinstance(data, dict):
            if "validation_status" not in data:
                data["validation_status"] = "valid"
            if "validation_message" not in data:
                data["validation_message"] = None

    # 2. Permission Number pattern check
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
        f_data = fields.get(key)
        if f_data and f_data.get("value"):
            val = f_data["value"]
            parsed = parse_numeric_area(val)
            if parsed is None:
                f_data["validation_status"] = "invalid"
                f_data["validation_message"] = "Area value must contain a number"

    # 4. Cross-field consistency (Built-up Area vs Land Area)
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


def analyze_document(text_or_path: str | Path) -> dict[str, Any]:
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

    # Import and run modular extractors
    from .extractors.agreement_extractor import AgreementExtractor
    from .extractors.schedule_extractor import ScheduleExtractor
    from .extractors.work_order_extractor import WorkOrderExtractor
    from .extractors.receipt_extractor import ReceiptExtractor
    from .extractors.noc_extractor import NOCExtractor

    agreement_ext = AgreementExtractor()
    schedule_ext = ScheduleExtractor()
    wo_ext = WorkOrderExtractor()
    receipt_ext = ReceiptExtractor()
    noc_ext = NOCExtractor()

    fields = {}
    fields.update(agreement_ext.extract(markdown_text, page_results))
    fields.update(schedule_ext.extract(markdown_text, page_results))
    fields.update(wo_ext.extract(markdown_text, page_results))
    fields.update(receipt_ext.extract(markdown_text, page_results))
    fields.update(noc_ext.extract(markdown_text, page_results))

    # Invoke Gemini fallback
    from .gemini_service import GeminiService
    gemini_service = GeminiService()
    fields = gemini_service.fallback_low_confidence_fields(fields, markdown_text)

    # Apply validations
    fields = validate_extracted_fields(fields)

    # Calculate root-level confidence
    non_null_confs = [
        f["final_confidence"] for f in fields.values() 
        if isinstance(f, dict) and f.get("value") is not None
    ]
    fields["confidence"] = sum(non_null_confs) / len(non_null_confs) if non_null_confs else 0.0

    return fields