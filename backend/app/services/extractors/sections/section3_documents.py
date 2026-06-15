from typing import Any
import re
from app.services.extractors.base import extract_field_by_labels, create_scored_field

def extract_section3(text: str) -> dict[str, Any]:
    """
    Extracts Document related fields (Document Number, Registration Details, Permission Number).
    """
    try:
        # 1. Document Number Extraction
        # Look for labels like Document Number, Doc No, Reg No, etc.
        doc_num_labels = [
            "Document Number", "DocumentNumber", "Doc No.", "Doc No", "DocNo", "Registration No.", "Reg No.", "RegNo."
        ]
        doc_num_res = extract_field_by_labels(text, doc_num_labels, "document_number")

        # 2. Registration Details Extraction
        # Look for labels like Registration Details, Registered At, etc.
        reg_details_labels = [
            "Registration Details", "RegistrationDetails", "Registered At", "RegisteredAt", "registration details", "registered at"
        ]
        reg_details_res = extract_field_by_labels(text, reg_details_labels, "registration_details")

        # 3. Permission Number Extraction
        # Extracts permission numbers from Work Orders, using pattern searches
        permission_number = _extract_permission_number(text)
        permission_res = create_scored_field(permission_number)
        if permission_number:
            permission_res["regex_confidence"] = 0.95
            permission_res["final_confidence"] = 0.95

        return {
            "document_number": doc_num_res,
            "registration_details": reg_details_res,
            "permission_number": permission_res
        }
    except Exception:
        return {
            "document_number": create_scored_field(None),
            "registration_details": create_scored_field(None),
            "permission_number": create_scored_field(None)
        }

def _extract_permission_number(text: str) -> str | None:
    # clean text
    clean_text = text.replace("|", " ")
    
    MONTH_ABBRS = {"jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"}
    
    def is_date_or_stamp(val: str) -> bool:
        val_clean = val.strip().lower()
        if re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", val_clean):
            return True
        if re.search(r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b", val_clean):
            return True
        for m in MONTH_ABBRS:
            if val_clean.startswith(m) and len(val_clean) > len(m):
                tail = val_clean[len(m):]
                if re.match(r"^[-/.\s]\d+", tail):
                    return True
        return False

    def is_valid_permit(v: str) -> bool:
        if not re.search(r"\d", v):
            return False
        if re.search(r"[a-z]", v):
            return False
        return True

    # Look for patterns with indicators followed/preceded by permission number
    keyword_patterns = [
        r"([A-Z0-9][A-Z0-9/\-_.]+)\s*(?:PERMIT No\.|PERMIT|FILE No\.|File Number|Permission Number|Permission No\.?)",
        r"(?:Construction Permission Approved By|Construction Permission|Vide File No\.|File No\.|Permission Number|Permission No\.?|Permission|PERMIT No\.|PERMIT)\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-_.]+)",
    ]

    for pattern in keyword_patterns:
        for match in re.finditer(pattern, clean_text, flags=re.IGNORECASE | re.MULTILINE):
            groups = [group for group in match.groups() if group]
            if groups:
                val = groups[0].strip()
                if not is_date_or_stamp(val) and is_valid_permit(val):
                    return re.sub(r"\s+", " ", val).strip()

    # Look line by line
    for line in clean_text.splitlines():
        if re.search(r"permission|file no|vide file no|permit no|permit|construction permission", line, flags=re.IGNORECASE):
            tokens = re.findall(r"[A-Z0-9][A-Z0-9/\-_.]+", line, flags=re.IGNORECASE)
            if tokens:
                for token in reversed(tokens):
                    if ('/' in token or '-' in token) and len(token) > 5:
                        if not is_date_or_stamp(token) and is_valid_permit(token):
                            return re.sub(r"\s+", " ", token).strip()
                last_token = tokens[-1]
                if not is_date_or_stamp(last_token) and is_valid_permit(last_token):
                    return re.sub(r"\s+", " ", last_token).strip()

    # Fallback to general patterns
    fallback = re.search(r"\b[A-Z0-9]{2,}[/-][A-Z0-9/-]{2,}\b", clean_text, flags=re.IGNORECASE)
    if fallback:
        val = fallback.group(0)
        if not is_date_or_stamp(val) and is_valid_permit(val):
            return re.sub(r"\s+", " ", val).strip()
    return None
