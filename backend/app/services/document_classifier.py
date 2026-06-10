from __future__ import annotations

import re
from typing import Any


def classify_document(filename: str, text: str) -> str | None:
    fn_upper = filename.upper()
    text_upper = text.upper()

    # 1. Classify by filename matches first (strongest indicator)
    if "AOS" in fn_upper or "AGREEMENT OF SALE" in fn_upper or "AGREEMENT FOR SALE" in fn_upper:
        return "AOS"
    if "PERMISSION" in fn_upper or "PERMIT" in fn_upper or "GHMC" in fn_upper:
        return "PERMISSION"
    if "RERA" in fn_upper:
        return "RERA"
    if "WORK ORDER" in fn_upper or "WO" in fn_upper or "WORKORDER" in fn_upper:
        return "WO"
    if "SALE DEED" in fn_upper or "DEED OF SALE" in fn_upper or "DAGPA" in fn_upper:
        return "SALE_DEED"

    # 2. Classify by key content keywords
    # AOS Keywords
    aos_keywords = ["VENDEE", "AGREEMENT OF SALE", "AGREEMENT FOR SALE", "PURCHASER", "SECOND PART"]
    if any(kw in text_upper for kw in aos_keywords):
        return "AOS"

    # Permission Keywords
    perm_keywords = ["PERMIT NO", "GHMC", "BUILDING PERMISSION", "FILE NO", "COMMISSIONER"]
    if any(kw in text_upper for kw in perm_keywords):
        return "PERMISSION"

    # RERA Keywords
    rera_keywords = ["RERA REGISTRATION NUMBER", "RERA REG", "RERA NO", "RERA REGISTRATION"]
    if any(kw in text_upper for kw in rera_keywords):
        return "RERA"

    # WO Keywords
    wo_keywords = ["WORK ORDER", "PLACED ON", "WO NO", "PURCHASE ORDER"]
    if any(kw in text_upper for kw in wo_keywords):
        return "WO"

    # Sale Deed Keywords
    sale_keywords = ["SALE DEED", "DEED OF SALE", "DAGPA"]
    if any(kw in text_upper for kw in sale_keywords):
        return "SALE_DEED"

    # 3. Weak matches / Fallbacks
    if "RERA" in text_upper:
        return "RERA"
    if "AGREEMENT" in text_upper:
        return "AOS"
    if "PERMIT" in text_upper:
        return "PERMISSION"
    if "WORK" in text_upper and "ORDER" in text_upper:
        return "WO"
    if "DEED" in text_upper:
        return "SALE_DEED"

    return None


class DocumentClassifier:
    def classify_bundle(self, document_bundle: dict[str, dict[str, Any]]) -> dict[str, str]:
        """
        Takes a bundle of document details and categorizes them.
        Returns a dict of {doc_type: concatenated_cleaned_text}
        """
        classified: dict[str, str] = {}
        for source_name, data in document_bundle.items():
            filename = data.get("file_name", source_name)
            text = data.get("text", "")
            doc_type = classify_document(filename, text)

            if doc_type:
                if doc_type in classified:
                    classified[doc_type] += "\n\n" + text
                else:
                    classified[doc_type] = text

        return classified
