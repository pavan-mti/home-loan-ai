from typing import Any
from app.services.extractors.base import extract_field_by_labels, create_scored_field

def extract_section14(text: str) -> dict[str, Any]:
    """
    Extracts Government Enactment details.
    """
    try:
        enact_labels = ["Govt Enactment Details", "Enactment Details", "Govt Enactment"]
        enact_res = extract_field_by_labels(text, enact_labels, "govt_enactment_details")

        govt_land_labels = ["Is Govt Land", "Govt Land Status"]
        govt_land_res = extract_field_by_labels(text, govt_land_labels, "is_govt_land")

        return {
            "govt_enactment_details": enact_res,
            "is_govt_land": govt_land_res
        }
    except Exception:
        return {
            "govt_enactment_details": create_scored_field(None),
            "is_govt_land": create_scored_field(None)
        }
