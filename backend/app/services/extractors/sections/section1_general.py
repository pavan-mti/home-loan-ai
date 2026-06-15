from typing import Any
from app.services.extractors.base import create_scored_field

def extract_section1(text: str) -> dict[str, Any]:
    """
    Extracts General Section fields.
    This section contains default values or current date values that are usually
    user inputs, rather than content from the OCR document.
    """
    try:
        return {
            "valuation_purpose": create_scored_field("Purchase Loan", ocr_confidence=1.0, regex_confidence=1.0, final_confidence=1.0),
            "inspection_date": create_scored_field(None),
            "valuation_date": create_scored_field(None)
        }
    except Exception:
        return {
            "valuation_purpose": create_scored_field(None),
            "inspection_date": create_scored_field(None),
            "valuation_date": create_scored_field(None)
        }
