from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from docx import Document
from docx.document import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph

from ..schemas import TemplateContentSpec, TemplateFieldSpec, TemplateSectionSpec, TemplateTableSpec


def classify_field_type(field_name: str) -> str:
    name_clean = field_name.strip()
    name_upper = name_clean.upper()
    
    # 1. SECTION: starts with SECTION or matches roman numeral headings
    if name_upper.startswith("SECTION"):
        return "SECTION"
    
    # Roman numeral headings (e.g. I. GENERAL, VII. VALUATION SUMMARY)
    if re.match(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)\.?\s+", name_upper) or re.match(r"^(I|II|III|IV|V|VI|VII|VIII|IX|X)\.?$", name_upper):
        return "SECTION"
        
    # 2. MANUAL: contains keywords
    manual_keywords = {
        "guideline value", "fair market value", "distress value", "realizable value",
        "remarks", "risk", "valuer", "marketability", "recommendation"
    }
    name_lower = name_clean.lower()
    if any(kw in name_lower for kw in manual_keywords):
        return "MANUAL"
        
    return "AUTO"


def _iter_block_items(document: DocxDocument) -> Iterable[Paragraph | Table]:
    for child in document.element.body.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, document)
        elif child.tag.endswith("}tbl"):
            yield Table(child, document)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return slug or "field"


def _is_heading(paragraph: Paragraph) -> bool:
    text = _clean_text(paragraph.text)
    if not text:
        return False
    style_name = getattr(paragraph.style, "name", "") or ""
    if style_name.lower().startswith("heading"):
        return True
    words = text.split()
    return len(words) <= 8 and text.isupper()


def _normalize_section_name(text: str) -> str:
    return _clean_text(text).upper()


def _parse_keywords(value: str) -> list[str]:
    keywords = re.split(r"[,;/\n]", value)
    return [_clean_text(keyword) for keyword in keywords if _clean_text(keyword)]


def _normalize_document_source(value: str | None) -> str | None:
    if not value:
        return None
    candidate = _clean_text(value)
    candidate = candidate.split(".")[0]
    return candidate.upper() if candidate else None


def _split_key_value(text: str) -> tuple[str | None, str | None]:
    match = re.match(r"^([^:=]+)[:=](.+)$", text)
    if not match:
        return None, None
    return _clean_text(match.group(1)), _clean_text(match.group(2))


def _parse_metadata_line(field: dict[str, Any], line: str) -> None:
    key, value = _split_key_value(line)
    if not key or value is None:
        return
    normalized = key.lower()
    if normalized in {"source document", "document source", "source"}:
        field["document_source"] = _normalize_document_source(value)
    elif normalized == "keywords":
        field["keywords"] = _parse_keywords(value)
    elif normalized in {"static value", "static"}:
        field["static_value"] = value
    elif normalized in {"dynamic value", "dynamic"}:
        field["dynamic_value"] = value
    elif normalized in {"field type", "type"}:
        field["field_type"] = value.lower()
    elif normalized in {"label", "field label"}:
        field["label"] = value
    elif normalized in {"field code", "code"}:
        field["field_code"] = _slugify(value)
    elif normalized.startswith("nested"):
        field.setdefault("nested_fields", [])
        nested_field = _build_field_from_text(value)
        field["nested_fields"].append(nested_field)


def _build_field_from_text(text: str) -> dict[str, Any]:
    lines = [_clean_text(line) for line in text.splitlines() if _clean_text(line)]
    if not lines:
        return {}

    field: dict[str, Any] = {
        "label": lines[0],
        "field_code": _slugify(lines[0]),
        "document_source": None,
        "keywords": [],
        "field_type": "text",
        "static_value": None,
        "dynamic_value": None,
        "raw_text": "\n".join(lines),
        "nested_fields": [],
    }

    first_key, first_value = _split_key_value(lines[0])
    if first_key and first_value is not None:
        field["label"] = first_key
        field["field_code"] = _slugify(first_key)
        if first_key.lower() in {"source document", "document source"}:
            field["document_source"] = _normalize_document_source(first_value)
        elif first_key.lower() == "keywords":
            field["keywords"] = _parse_keywords(first_value)
        else:
            field["static_value"] = first_value

    for line in lines[1:]:
        _parse_metadata_line(field, line)

    if field["nested_fields"]:
        field["field_type"] = "group"
    elif field.get("static_value") and not field.get("keywords"):
        field["field_type"] = "static"
    elif field.get("document_source") or field.get("keywords"):
        field["field_type"] = field.get("field_type") or "text"

    return field


def _parse_paragraph_blocks(paragraphs: list[str]) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    block: list[str] = []

    def flush_block() -> None:
        nonlocal block
        if not block:
            return
        text = "\n".join(block).strip()
        if text:
            fields.append(_build_field_from_text(text))
        block = []

    for paragraph in paragraphs:
        if not paragraph:
            flush_block()
            continue
        if re.match(r"^[•\-*]", paragraph):
            block.append(paragraph.lstrip("•-* "))
            continue
        if _split_key_value(paragraph)[0] and block and len(block) == 1 and not _split_key_value(block[0])[0]:
            flush_block()
        block.append(paragraph)

    flush_block()
    return [field for field in fields if field.get("label")]


def _table_to_spec(table: Table) -> TemplateTableSpec:
    rows = [[_clean_text(cell.text) for cell in row.cells] for row in table.rows]
    headers = rows[0] if rows else []
    return TemplateTableSpec(name=None, headers=headers, rows=rows)


def _is_metadata_or_nested_line(text: str) -> bool:
    key, _ = _split_key_value(text)
    if not key:
        return False
    normalized = key.lower()
    if normalized in {
        "source document", "document source", "source", "keywords",
        "static value", "static", "dynamic value", "dynamic",
        "field type", "type", "label", "field label", "field code", "code"
    }:
        return True
    return False


def parse_template_docx(file_path: Path) -> dict[str, Any]:
    document = Document(str(file_path))
    sections: list[dict[str, Any]] = []
    current_section: dict[str, Any] = {"name": "GENERAL", "fields": [], "tables": []}

    current_field: dict[str, Any] | None = None

    def flush_current_field() -> None:
        nonlocal current_field, current_section
        if not current_field:
            return
        if current_field.get("nested_fields"):
            current_field["field_type"] = "group"
        else:
            current_field["field_type"] = classify_field_type(current_field.get("label") or "")
        current_section["fields"].append(current_field)
        current_field = None

    def start_field(text: str) -> None:
        nonlocal current_field
        base = _build_field_from_text(text)
        current_field = {
            "label": base.get("label"),
            "field_code": base.get("field_code"),
            "document_source": base.get("document_source"),
            "keywords": base.get("keywords", []),
            "field_type": classify_field_type(base.get("label") or ""),
            "static_value": base.get("static_value"),
            "dynamic_value": base.get("dynamic_value"),
            "raw_text": base.get("raw_text"),
            "nested_fields": base.get("nested_fields", []),
        }

    for block in _iter_block_items(document):
        if isinstance(block, Paragraph):
            text = _clean_text(block.text)
            if not text:
                flush_current_field()
                continue
            if _is_heading(block):
                flush_current_field()
                if current_section["fields"] or current_section["tables"] or current_section["name"] != "GENERAL":
                    sections.append(current_section)
                current_section = {"name": _normalize_section_name(text), "fields": [], "tables": []}
                current_field = None
            elif _is_metadata_or_nested_line(text):
                if current_field is None:
                    start_field(text)
                else:
                    _parse_metadata_line(current_field, text)
            elif _split_key_value(text)[0] or text.endswith(":"):
                flush_current_field()
                start_field(text)
            else:
                if current_field is None:
                    start_field(text)
                else:
                    current_field["raw_text"] = f"{current_field.get('raw_text', '')}\n{text}".strip()
        else:
            flush_current_field()
            current_section["tables"].append(_table_to_spec(block).model_dump())

    flush_current_field()
    if current_section["fields"] or current_section["tables"] or current_section["name"] != "GENERAL":
        sections.append(current_section)

    if not sections:
        sections = [current_section]

    for section in sections:
        if not section.get("fields"):
            generated_fields = []
            seen_codes = set()
            for table in section.get("tables", []):
                rows = table.get("rows", [])
                for row in rows:
                    if not row or len(row) < 1:
                        continue
                    first_cell = row[0].strip()
                    if not first_cell:
                        continue
                    field_code = _slugify(first_cell)
                    if field_code in seen_codes:
                        continue
                    seen_codes.add(field_code)
                    generated_fields.append({
                        "label": first_cell,
                        "field_code": field_code,
                        "field_type": classify_field_type(first_cell),
                        "keywords": [first_cell],
                    })
            section["fields"] = generated_fields

    content = TemplateContentSpec(sections=sections)
    print("\n========== FINAL TEMPLATE CONTENT ==========")
    print(content.model_dump())
    print("===========================================\n")
    return content.model_dump()


def parse_template_pdf(file_path: Path) -> dict[str, Any]:
    import pdfplumber

    sections: list[dict[str, Any]] = []
    current_section: dict[str, Any] = {"name": "GENERAL", "fields": [], "tables": []}
    current_field: dict[str, Any] | None = None

    def flush_current_field() -> None:
        nonlocal current_field, current_section
        if not current_field:
            return
        if current_field.get("nested_fields"):
            current_field["field_type"] = "group"
        elif current_field.get("static_value") and not current_field.get("keywords"):
            current_field["field_type"] = "static"
        elif current_field.get("document_source") or current_field.get("keywords"):
            current_field["field_type"] = current_field.get("field_type") or "text"
        current_section["fields"].append(current_field)
        current_field = None

    def start_field(text: str) -> None:
        nonlocal current_field
        base = _build_field_from_text(text)
        current_field = {
            "label": base.get("label"),
            "field_code": base.get("field_code"),
            "document_source": base.get("document_source"),
            "keywords": base.get("keywords", []),
            "field_type": base.get("field_type", "text"),
            "static_value": base.get("static_value"),
            "dynamic_value": base.get("dynamic_value"),
            "raw_text": base.get("raw_text"),
            "nested_fields": base.get("nested_fields", []),
        }

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            # 1. Extract and process tables
            tables = page.extract_tables() or []
            for table in tables:
                cleaned_rows = []
                for row in table:
                    cleaned_row = []
                    for cell in row:
                        cleaned_row.append(_clean_text(cell) if cell else "")
                    cleaned_rows.append(cleaned_row)
                headers = cleaned_rows[0] if cleaned_rows else []
                current_section["tables"].append({
                    "name": None,
                    "headers": headers,
                    "rows": cleaned_rows
                })

            # 2. Extract and process text
            text = page.extract_text()
            if not text:
                continue
            for line in text.splitlines():
                line = _clean_text(line)
                if not line:
                    flush_current_field()
                    continue
                
                # Heading detection: uppercase and short
                words = line.split()
                is_heading = len(words) <= 8 and line.isupper()

                if is_heading:
                    flush_current_field()
                    if current_section["fields"] or current_section["tables"] or current_section["name"] != "GENERAL":
                        sections.append(current_section)
                    current_section = {"name": _normalize_section_name(line), "fields": [], "tables": []}
                    current_field = None
                elif _is_metadata_or_nested_line(line):
                    if current_field is None:
                        start_field(line)
                    else:
                        _parse_metadata_line(current_field, line)
                elif _split_key_value(line)[0] or line.endswith(":"):
                    flush_current_field()
                    start_field(line)
                else:
                    if current_field is None:
                        start_field(line)
                    else:
                        current_field["raw_text"] = f"{current_field.get('raw_text', '')}\n{line}".strip()

    flush_current_field()
    if current_section["fields"] or current_section["tables"] or current_section["name"] != "GENERAL":
        sections.append(current_section)

    if not sections:
        sections = [current_section]

    content = TemplateContentSpec(sections=sections)
    return content.model_dump()