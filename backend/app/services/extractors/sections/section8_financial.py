from typing import Any
from app.services.extractors.base import create_scored_field

def extract_section8(text: str) -> dict[str, Any]:
    """
    Extracts Financial/Valuation details.
    """
    try:
        return {
            "market_value": create_scored_field(None),
            "guideline_value": create_scored_field(None)
        }
    except Exception:
        return {
            "market_value": create_scored_field(None),
            "guideline_value": create_scored_field(None)
        }
