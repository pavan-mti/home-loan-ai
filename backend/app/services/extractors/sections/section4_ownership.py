from typing import Any
from app.services.extractors.base import extract_field_by_labels, create_scored_field

def extract_section4(text: str) -> dict[str, Any]:
    """
    Extracts Ownership related fields (Applicant Name, Owner Name).
    """
    try:
        # 1. Applicant Name Extraction
        # Look for labels like Name of Applicant, Applicant Name, Sri/Smt, Mr/Mrs.
        applicant_labels = [
            "Name of Applicant", "Applicant Name", "ApplicantName", "Applicant", "Sri/Smt.", "Mrs.", "Mr."
        ]
        applicant_res = extract_field_by_labels(text, applicant_labels, "applicant_name")

        # 2. Owner Name Extraction
        # Look for labels like Owner Name, Name of Owner, Land Owner.
        owner_labels = [
            "Name of Owner", "Owner Name", "Landowner", "Land Owner", "Vendor", "Developer"
        ]
        owner_res = extract_field_by_labels(text, owner_labels, "owner_name")

        return {
            "applicant_name": applicant_res,
            "owner_name": owner_res
        }
    except Exception:
        return {
            "applicant_name": create_scored_field(None),
            "owner_name": create_scored_field(None)
        }
