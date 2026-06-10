from __future__ import annotations

import re


def clean_text(raw_text: str) -> str:
    if not raw_text:
        return ""

    # Remove non-printable characters except common whitespace
    cleaned = "".join(ch for ch in raw_text if ch.isprintable() or ch in "\n\r\t")

    # Normalize line breaks
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")

    lines = cleaned.split("\n")
    cleaned_lines = []
    for line in lines:
        # Normalize double/multiple spaces and tabs
        cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
        # Filter out common single-character OCR artifacts (noise lines)
        if len(cleaned_line) == 1 and cleaned_line in "|._~-=\\`":
            continue
        cleaned_lines.append(cleaned_line)

    cleaned = "\n".join(cleaned_lines)

    # Limit consecutive newlines to at most double newlines to keep text readable
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()
