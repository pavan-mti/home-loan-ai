from __future__ import annotations

import re
from typing import Any
from ..candidate_model import Candidate

STOPWORDS = {
    "to", "and", "or", "of", "for", "with", "the", "by", "its", "our",
    "your", "my", "their", "an", "a", "in", "at", "on", "as", "is",
    "are", "was", "were", "be", "been", "being", "he", "she", "it",
    "they", "we", "you", "i", "this", "that", "these", "those",
    "including", "such", "also", "from", "which", "regard", "time",
    "regards", "between", "nor", "any", "said"
}

PUNCTUATION_CHARS = set(".,:;!?-_–—=+|/\\()[]{}#*`~ '\"")

class CandidateQualityGate:
    def __init__(
        self,
        min_label_len: int = 2,
        min_value_len: int = 1,
        max_value_len: int = 400
    ):
        self.min_label_len = min_label_len
        self.min_value_len = min_value_len
        self.max_value_len = max_value_len

    def validate(self, candidate: Candidate) -> bool:
        if not candidate:
            return False

        label = (candidate.label or "").strip()
        val = (candidate.value or "").strip()

        # 1. Reject if label or value is empty
        if not label or not val:
            return False

        # 2. Reject if punctuation only
        if set(label).issubset(PUNCTUATION_CHARS) or set(val).issubset(PUNCTUATION_CHARS):
            return False

        # 3. Check minimum lengths
        if len(label) < self.min_label_len and not label.isalnum():
            return False

        if len(val) < self.min_value_len:
            return False
            
        # Reject single letter non-digits as values (e.g., "R", "T", "X")
        if len(val) == 1 and not val.isdigit():
            return False

        if len(val) > self.max_value_len:
            return False

        # 4. Reject stopwords as exact value or label
        val_lc = val.lower()
        label_lc = label.lower()

        if label_lc in STOPWORDS:
            return False

        if val_lc in STOPWORDS:
            return False

        # 5. Must have at least one alphanumeric character
        if not any(c.isalnum() for c in label) or not any(c.isalnum() for c in val):
            return False

        # 6. Reject OCR garbage / repeated symbols
        if re.search(r'(.)\1{4,}', val) or re.search(r'(.)\1{4,}', label):
            return False

        # 7. Reject obvious incomplete sentence fragments
        if val.startswith((",", "(including", "(includes")):
            return False

        if val_lc.endswith(("between:-", "and between:-", "at the time of registration.")):
            return False

        return True
