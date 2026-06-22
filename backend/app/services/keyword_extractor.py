from __future__ import annotations

import re
from typing import Any


def extract_by_keywords(text: str, keywords: list[str]) -> dict[str, Any]:
    """
    Looks for keywords within the text, extracts the text following it,
    and returns it with confidence.
    """
    if not text or not keywords:
        return {"value": None, "confidence": 0.0}

    for keyword in keywords:
        if not keyword or not keyword.strip():
            continue

        escaped = re.escape(keyword.strip())
        
        # 1. Look for inline matches: Keyword followed by delimiter and characters on the same line
        # Accept letters, numbers, typical punctuation like commas, slashes, hyphens, brackets, quotes.
        pattern = rf"{escaped}\s*[:\-=–—]?\s*([A-Za-z0-9,./()\'\"\-& ]{{2,150}})"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = re.sub(r"\s+", " ", match.group(1)).strip()
            value = value.strip(":,.-= ")
            # Basic validation to filter out junk single chars or excessively long sentences
            if value and len(value) > 2 and len(value) < 150:
                return {"value": value, "confidence": 0.92}

        # 2. Check line-by-line fallback
        lines = text.split("\n")
        for idx, line in enumerate(lines):
            if re.search(escaped, line, flags=re.IGNORECASE):
                # Search if there is text after it on the same line
                inline_match = re.search(rf"{escaped}\s*[:\-=–—]?\s*(.*)", line, flags=re.IGNORECASE)
                if inline_match:
                    val = inline_match.group(1).strip()
                    if val and len(val) > 2 and len(val) < 150:
                        return {"value": val, "confidence": 0.90}
                
                # Check next line (if the keyword acts as a label above the value)
                if idx + 1 < len(lines):
                    next_line = lines[idx + 1].strip()
                    # If next line is not a separator/noise, doesn't contain a colon, and is reasonable length
                    if next_line and len(next_line) > 2 and ":" not in next_line and len(next_line) < 150:
                        return {"value": next_line, "confidence": 0.85}

    return {"value": None, "confidence": 0.0}