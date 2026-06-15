from typing import Any
from app.services.extractors.base import create_scored_field

def extract_section6(text: str) -> dict[str, Any]:
    """
    Extracts Prohibited transaction details.
    """
    try:
        return {
            "prohibited_transaction": create_scored_field(None),
            "is_prohibited": create_scored_field(None)
        }
    except Exception:
        return {
            "prohibited_transaction": create_scored_field(None),
            "is_prohibited": create_scored_field(None)
        }
