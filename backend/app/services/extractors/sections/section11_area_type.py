from typing import Any
from app.services.extractors.base import extract_field_by_labels, create_scored_field

def extract_section11(text: str) -> dict[str, Any]:
    """
    Extracts specific Area Type fields (Super Built-up Area, Carpet Area).
    """
    try:
        # Super Built-up Area
        super_built_up_labels = ["Super Built-up Area", "Super Built Up Area", "SBA"]
        super_built_up_res = extract_field_by_labels(text, super_built_up_labels, "super_built_up_area", is_area_field=True)

        # Carpet Area
        carpet_labels = ["Carpet Area", "CarpetArea"]
        carpet_res = extract_field_by_labels(text, carpet_labels, "carpet_area", is_area_field=True)

        return {
            "super_built_up_area": super_built_up_res,
            "carpet_area": carpet_res
        }
    except Exception:
        return {
            "super_built_up_area": create_scored_field(None),
            "carpet_area": create_scored_field(None)
        }
