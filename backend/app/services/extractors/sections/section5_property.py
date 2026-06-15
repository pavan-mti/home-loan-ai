from typing import Any
from app.services.extractors.base import extract_field_by_labels, create_scored_field

def extract_section5(text: str) -> dict[str, Any]:
    """
    Extracts Property Description fields (Built-up Area, Land Area, Property Description).
    """
    try:
        # 1. Built-up Area Extraction
        built_up_labels = [
            "Built-up Area", "Built Up Area", "Builtup Area", "Built-upArea", "BuiltUpArea", "built-up area as per sanctioned plan"
        ]
        built_up_res = extract_field_by_labels(text, built_up_labels, "built_up_area", is_area_field=True)

        # 2. Land Area Extraction
        land_labels = [
            "Land Area", "LandArea", "Extent of Land", "Plot Area", "PlotArea"
        ]
        land_res = extract_field_by_labels(text, land_labels, "land_area", is_area_field=True)

        # 3. Property Description Extraction
        desc_labels = [
            "Property Description", "Description of Property", "Schedule of Property", "Details of Property"
        ]
        desc_res = extract_field_by_labels(text, desc_labels, "property_description")

        return {
            "built_up_area": built_up_res,
            "land_area": land_res,
            "property_description": desc_res
        }
    except Exception:
        return {
            "built_up_area": create_scored_field(None),
            "land_area": create_scored_field(None),
            "property_description": create_scored_field(None)
        }
