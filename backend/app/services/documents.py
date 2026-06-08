from __future__ import annotations

import io
import json
import os
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from fastapi import UploadFile

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional dependency guard
    OpenAI = None


STORAGE_ROOT = Path(__file__).resolve().parents[2] / "storage"
UPLOAD_ROOT = STORAGE_ROOT / "uploads"


def _ensure_directories() -> None:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


def save_upload(upload: UploadFile, subfolder: str) -> Path:
    _ensure_directories()
    target_dir = UPLOAD_ROOT / subfolder
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(upload.filename or "document").name
    target_path = target_dir / safe_name
    data = upload.file.read()
    target_path.write_bytes(data)
    upload.file.seek(0)
    return target_path


def _read_docx_bytes(data: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        document_xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(document_xml)
    texts: list[str] = []
    for element in root.iter():
        if element.tag.endswith("}t") and element.text:
            texts.append(element.text)
    return " ".join(texts)


def _read_text_from_pdf_bytes(data: bytes) -> str:
    try:
        import fitz  # type: ignore
    except Exception:
        fitz = None

    if fitz is not None:
        document = fitz.open(stream=data, filetype="pdf")
        chunks = [page.get_text("text") for page in document]
        combined = "\n".join(chunks).strip()
        if combined:
            return combined

        try:
            import pytesseract  # type: ignore
            from PIL import Image  # type: ignore
        except Exception:
            return combined

        ocr_chunks: list[str] = []
        for page in document:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            ocr_chunks.append(pytesseract.image_to_string(image))
        return "\n".join(ocr_chunks).strip()

    try:
        from PyPDF2 import PdfReader  # type: ignore
    except Exception:
        PdfReader = None

    if PdfReader is not None:
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()

    return data.decode("latin-1", errors="ignore")


def _read_text_from_image_bytes(data: bytes) -> str:
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
    except Exception:
        return data.decode("latin-1", errors="ignore")

    image = Image.open(io.BytesIO(data))
    return pytesseract.image_to_string(image)


def extract_text_from_upload(file_path: Path) -> str:
    data = file_path.read_bytes()
    suffix = file_path.suffix.lower()

    if suffix == ".docx":
        return _read_docx_bytes(data)
    if suffix == ".pdf":
        return _read_text_from_pdf_bytes(data)
    if suffix in {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}:
        return _read_text_from_image_bytes(data)
    return data.decode("utf-8", errors="ignore")


def _collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _find_value(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            groups = [group for group in match.groups() if group]
            if groups:
                return _collapse_whitespace(groups[0])
    return None


def extract_permission_number(text: str) -> str | None:
    keyword_patterns = [
        r"(?:Construction Permission Approved By|Construction Permission|Vide File No\.|File No\.|Permission Number|Permission No\.?|Permission)\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-_.() ]{2,})",
        r"(?:Permission Number|Permission No\.?|File No\.)\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-_.() ]{2,})",
    ]

    normalized = _collapse_whitespace(text)
    extracted = _find_value(keyword_patterns, normalized)
    if extracted:
        return extracted

    for line in text.splitlines():
        if re.search(r"permission|file no|vide file no|construction permission", line, flags=re.IGNORECASE):
            tokens = re.findall(r"[A-Z0-9][A-Z0-9/\-_.()]{2,}", line, flags=re.IGNORECASE)
            if tokens:
                return _collapse_whitespace(tokens[-1])

    fallback = re.search(r"\b[A-Z0-9]{2,}[/-][A-Z0-9/-]{2,}\b", text, flags=re.IGNORECASE)
    return fallback.group(0) if fallback else None


def _look_for_label(text: str, labels: list[str]) -> str | None:
    for label in labels:
        pattern = rf"{re.escape(label)}\s*[:\-]?\s*([^\n,;]+)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _collapse_whitespace(match.group(1))
    return None


def _openai_extract(text: str) -> dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None

    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=(
                "Extract the valuation document fields as JSON with keys: "
                "applicant_name, survey_number, plot_number, permission_number, property_address, built_up_area, land_area, document_number, registration_details, confidence. "
                "Only return JSON.\n\nDocument text:\n" + text[:12000]
            ),
        )
        parsed = json.loads(response.output_text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None


def analyze_document(text: str) -> dict[str, Any]:
    normalized = _collapse_whitespace(text)
    permission_number = extract_permission_number(text)

    fields = {
        "applicant_name": _look_for_label(normalized, ["Applicant Name", "Name of Applicant", "Applicant"]),
        "survey_number": _look_for_label(normalized, ["Survey Number", "Survey No.", "Survey No", "Sy No.", "Sy No"]),
        "plot_number": _look_for_label(normalized, ["Plot Number", "Plot No.", "Plot No"]),
        "permission_number": permission_number,
        "property_address": _look_for_label(normalized, ["Property Address", "Address", "Site Address"]),
        "built_up_area": _look_for_label(normalized, ["Built-up Area", "Built Up Area", "Builtup Area"]),
        "land_area": _look_for_label(normalized, ["Land Area", "Extent of Land", "Plot Area"]),
        "document_number": _look_for_label(normalized, ["Document Number", "Doc No.", "Doc No", "Registration No.", "Reg No."]),
        "registration_details": _look_for_label(normalized, ["Registration Details", "Registered At", "Registration"]),
        "confidence": 0.55 if permission_number else 0.35,
    }

    ai_fields = _openai_extract(text)
    if ai_fields:
        for key, value in ai_fields.items():
            if key in fields and value not in (None, ""):
                fields[key] = value
    return fields