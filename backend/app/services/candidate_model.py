from dataclasses import dataclass
from typing import Any

@dataclass
class Candidate:
    label: str
    value: str
    page: int | None = None
    bounding_box: Any | None = None
    ocr_confidence: float = 0.0
    extraction_strategy: str = ""
    source_line: int | None = None

    # Score fields
    semantic_score: float = 0.0
    fuzzy_score: float = 0.0
    context_score: float = 0.0
    validation_score: float = 1.0  # Default to no penalty
    final_score: float = 0.0
    explanation: str = ""

    # Discovery metadata fields
    section: str | None = None
    parent_heading: str | None = None
    context_window: str | None = None
    discovery_strategy: str = ""
