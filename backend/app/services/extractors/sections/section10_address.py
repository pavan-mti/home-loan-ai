from typing import Any
from app.services.extractors.base import extract_field_by_labels, create_scored_field

def extract_section10(text: str) -> dict[str, Any]:
    """
    Extracts property address.
    """
    try:
        address_labels = [
            "Property Address", "PropertyAddress", "Address", "Site Address", "R/o.", "R/o", "Resident of"
        ]
        address_res = extract_field_by_labels(text, address_labels, "property_address")

        return {
            "property_address": address_res
        }
    except Exception:
        return {
            "property_address": create_scored_field(None)
        }
