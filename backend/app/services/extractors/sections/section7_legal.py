from typing import Any
from app.services.extractors.base import create_scored_field

def extract_section7(text: str) -> dict[str, Any]:
    """
    Extracts Legal details.
    """
    try:
        return {
            "legal_disputes": create_scored_field(None),
            "is_disputed": create_scored_field(None)
        }
    except Exception:
        return {
            "legal_disputes": create_scored_field(None),
            "is_disputed": create_scored_field(None)
        }
