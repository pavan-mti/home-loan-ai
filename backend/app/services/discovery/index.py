from __future__ import annotations
import re
from typing import Any

class DocumentIndex:
    def __init__(self, document_text: str, page_results: list[dict[str, Any]] | None = None):
        self.document_text = document_text or ""
        self.page_results = page_results
        self.lines = [line.strip() for line in self.document_text.splitlines()]
        
        self._key_values = None
        self._tables = None
        self._sections = None

    @property
    def key_values(self) -> list[dict[str, Any]]:
        if self._key_values is None:
            self._key_values = self._build_key_values()
        return self._key_values

    @property
    def tables(self) -> list[list[dict[str, Any]]]:
        if self._tables is None:
            self._tables = self._build_tables()
        return self._tables

    @property
    def sections(self) -> list[dict[str, Any]]:
        if self._sections is None:
            self._sections = self._build_sections()
        return self._sections

    def get_section_for_line(self, line_num: int) -> dict[str, Any]:
        for sec in self.sections:
            if sec["start_line"] <= line_num <= sec["end_line"]:
                return sec
        return {"heading": None, "start_line": 0, "end_line": 0, "lines": []}

    def get_context_window(self, line_num: int, window_size: int = 5) -> str:
        line_idx = line_num - 1
        start = max(0, line_idx - window_size)
        end = min(len(self.lines), line_idx + window_size + 1)
        return "\n".join(self.lines[start:end])

    def _build_key_values(self) -> list[dict[str, Any]]:
        pairs = []
        sep_pattern = re.compile(r"^([^:\-=–—]{2,60})\s*[:\-–—=]\s*(.+)$")
        
        for idx, line in enumerate(self.lines):
            # Same line key-value
            match = sep_pattern.match(line)
            if match:
                key = match.group(1).strip()
                val = match.group(2).strip()
                # Clean leading punctuation dangles from val
                val = re.sub(r"^[:\-–—=\s]+", "", val).strip()
                if len(key) >= 2 and len(val) >= 2 and not key.lower().endswith("and between"):
                    pairs.append({
                        "label": key,
                        "value": val,
                        "line_num": idx + 1,
                        "type": "same_line"
                    })
            
            # Next line key-value
            if idx + 1 < len(self.lines):
                next_line = self.lines[idx + 1].strip()
                line_clean = line.strip()
                
                # Check if current line looks like a label
                if (2 <= len(line_clean) < 40 and 
                    not sep_pattern.match(line_clean) and 
                    not line_clean.replace(" ", "").isdigit() and
                    any(c.isalpha() for c in line_clean)):
                    
                    # Check if next line looks like a value
                    if (next_line and 
                        len(next_line) >= 2 and 
                        not sep_pattern.match(next_line) and
                        not next_line.endswith(":") and
                        len(next_line) < 250):
                        
                        pairs.append({
                            "label": line_clean.rstrip(":"),
                            "value": next_line,
                            "line_num": idx + 1,
                            "type": "next_line"
                        })
        return pairs

    def _build_tables(self) -> list[list[dict[str, Any]]]:
        tables = []
        current_table = []
        
        for idx, line in enumerate(self.lines):
            line_clean = line.strip()
            if not line_clean:
                if current_table:
                    tables.append(current_table)
                    current_table = []
                continue
                
            is_table_row = False
            parts = []
            if "|" in line_clean:
                is_table_row = True
                parts = [p.strip() for p in line_clean.split("|") if p.strip()]
            elif "  " in line_clean:
                split_parts = [p.strip() for p in re.split(r"\s{2,}", line_clean) if p.strip()]
                if len(split_parts) >= 2:
                    is_table_row = True
                    parts = split_parts
                    
            if is_table_row:
                # Skip separator line like |---|---|
                if all(all(c in ':-' for c in p) for p in parts if p):
                    continue
                current_table.append({
                    "line_num": idx + 1,
                    "parts": parts,
                    "raw": line_clean
                })
            else:
                if current_table:
                    tables.append(current_table)
                    current_table = []
                    
        if current_table:
            tables.append(current_table)
            
        return tables

    def _build_sections(self) -> list[dict[str, Any]]:
        sections = []
        current_section = {
            "heading": "Document Start",
            "start_line": 1,
            "lines": []
        }
        
        for idx, line in enumerate(self.lines):
            line_clean = line.strip()
            if not line_clean:
                continue
                
            is_header = False
            if line_clean.startswith("#"):
                is_header = True
            elif line_clean.isupper() and 4 <= len(line_clean) <= 60 and not line_clean.replace(" ", "").isdigit():
                is_header = True
            elif line_clean.endswith(":") and len(line_clean) < 40 and any(w in line_clean.lower() for w in ["details", "schedule", "information"]):
                is_header = True
                
            if is_header:
                current_section["end_line"] = idx
                sections.append(current_section)
                current_section = {
                    "heading": line_clean.lstrip("# ").rstrip(":").strip(),
                    "start_line": idx + 1,
                    "lines": []
                }
            current_section["lines"].append(line)
            
        current_section["end_line"] = len(self.lines)
        sections.append(current_section)
        return sections
