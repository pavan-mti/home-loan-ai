from __future__ import annotations

import re
from typing import Any


def extract_by_regex(field_code: str, text: str) -> dict[str, Any]:
    """
    Applies common regex pattern-matching rules for fields like
    permission_number, rera_number, survey_number.
    """
    if not text:
        return {"value": None, "confidence": 0.0}

    code = field_code.lower()
    patterns = []

    if "permission" in code or "permit" in code:
        patterns = [
            r"PERMIT\s*NO\.?\s*[:\s-]*\s*([A-Z0-9/\-_.()]{4,})",
            r"FILE\s*NO\.?\s*[:\s-]*\s*([A-Z0-9/\-_.()]{4,})",
            r"BUILDING\s*PERMISSION\s*NUMBER\s*[:\s-]*\s*([A-Z0-9/\-_.()]{4,})",
        ]
    elif "rera" in code:
        patterns = [
            r"RERA\s*(?:REGISTRATION|REG|NO)?\.?\s*[:\s-]*\s*([A-Z0-9/\-_.()]{4,})",
            r"RERA.*?([A-Z0-9/\-_.()]{4,})",
        ]
    elif "survey" in code:
        patterns = [
            r"SURVEY\s*NO\.?\s*[:\-]?\s*([A-Za-z0-9/\-,\s()]+)",
            r"SY\.?\s*NO\.?\s*[:\-]?\s*([A-Za-z0-9/\-,\s()]+)",
        ]
    elif "plot" in code:
        patterns = [
            r"PLOT\s*NO\.?\s*[:\-]?\s*([A-Za-z0-9/\-,\s()]+)",
        ]
    elif "flat" in code:
        patterns = [
            r"FLAT\s*NO\.?\s*[:\-]?\s*([A-Za-z0-9/\-,\s()]+)",
        ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            val = match.group(1).strip()
            # Remove leading symbols/delimiters
            val = re.sub(r"^[ :\-=]+", "", val)
            val = val.strip("., ")
            if val and len(val) >= 2:
                # Truncate lines for survey/plot numbers to keep output clean
                if "survey" in code or "plot" in code or "flat" in code:
                    val = val.split("\n")[0].strip()
                return {"value": val, "confidence": 0.95}

    return {"value": None, "confidence": 0.0}
