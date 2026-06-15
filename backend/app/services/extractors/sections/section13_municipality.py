from typing import Any
from app.services.extractors.base import extract_field_by_labels, create_scored_field

def extract_section13(text: str) -> dict[str, Any]:
    """
    Extracts Municipality information.
    """
    try:
        muni_labels = ["Municipality Name", "Municipality", "Corporation", "Gram Panchayat"]
        muni_res = extract_field_by_labels(text, muni_labels, "municipality_name")

        body_labels = ["Local Body Type", "Local Body"]
        body_res = extract_field_by_labels(text, body_labels, "local_body_type")

        return {
            "municipality_name": muni_res,
            "local_body_type": body_res
        }
    except Exception:
        return {
            "municipality_name": create_scored_field(None),
            "local_body_type": create_scored_field(None)
        }
