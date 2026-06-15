from typing import Any
from app.services.extractors.base import extract_field_by_labels, create_scored_field

def extract_section15(text: str) -> dict[str, Any]:
    """
    Extracts Boundaries (North, South, East, West).
    """
    try:
        north_labels = ["North", "Boundary North", "Bounded by North", "Northern Boundary"]
        north_res = extract_field_by_labels(text, north_labels, "boundary_north")

        south_labels = ["South", "Boundary South", "Bounded by South", "Southern Boundary"]
        south_res = extract_field_by_labels(text, south_labels, "boundary_south")

        east_labels = ["East", "Boundary East", "Bounded by East", "Eastern Boundary"]
        east_res = extract_field_by_labels(text, east_labels, "boundary_east")

        west_labels = ["West", "Boundary West", "Bounded by West", "Western Boundary"]
        west_res = extract_field_by_labels(text, west_labels, "boundary_west")

        return {
            "boundary_north": north_res,
            "boundary_south": south_res,
            "boundary_east": east_res,
            "boundary_west": west_res
        }
    except Exception:
        return {
            "boundary_north": create_scored_field(None),
            "boundary_south": create_scored_field(None),
            "boundary_east": create_scored_field(None),
            "boundary_west": create_scored_field(None)
        }
