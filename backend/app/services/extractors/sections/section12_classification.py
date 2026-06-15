from typing import Any
from app.services.extractors.base import extract_field_by_labels, create_scored_field

def extract_section12(text: str) -> dict[str, Any]:
    """
    Extracts Property Classification & Zone.
    """
    try:
        class_labels = ["Property Classification", "Classification of Property"]
        class_res = extract_field_by_labels(text, class_labels, "property_classification")

        zone_labels = ["Zone Type", "Zone"]
        zone_res = extract_field_by_labels(text, zone_labels, "zone_type")

        return {
            "property_classification": class_res,
            "zone_type": zone_res
        }
    except Exception:
        return {
            "property_classification": create_scored_field(None),
            "zone_type": create_scored_field(None)
        }
