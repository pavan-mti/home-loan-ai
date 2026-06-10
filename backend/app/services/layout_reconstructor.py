from __future__ import annotations
from typing import Any

class LayoutReconstructor:
    def reconstruct_page(self, page_data: dict[str, Any]) -> str:
        lines = page_data.get("lines", [])
        if not lines:
            return ""
            
        # If no bounding boxes are available (e.g. digital text extract), return sequential lines
        if not any(line.get("box") is not None and len(line.get("box")) > 0 for line in lines):
            return "\n".join(line.get("text", "") for line in lines)
            
        # 1. Parse bounding boxes to coordinates
        parsed_lines = []
        for line in lines:
            text = line.get("text", "").strip()
            if not text:
                continue
            box = line.get("box", [])
            if box is not None and len(box) == 4:
                x_coords = [pt[0] for pt in box]
                y_coords = [pt[1] for pt in box]
                x_min = min(x_coords)
                y_min = min(y_coords)
                x_max = max(x_coords)
                y_max = max(y_coords)
                w = x_max - x_min
                h = y_max - y_min
            else:
                x_min = 0
                y_min = 0
                w = 0
                h = 0
            
            parsed_lines.append({
                "text": text,
                "x": x_min,
                "y": y_min,
                "w": w,
                "h": h,
                "confidence": line.get("confidence", 1.0)
            })
            
        # 2. Group lines into rows by close vertical alignment (y-coordinate)
        rows: list[list[dict[str, Any]]] = []
        parsed_lines.sort(key=lambda l: l["y"])
        
        for line in parsed_lines:
            if not rows:
                rows.append([line])
            else:
                last_row = rows[-1]
                last_line = last_row[0]
                h_ref = max(last_line["h"], line["h"]) if last_line["h"] and line["h"] else 15
                # Group if vertical centers are close (within 60% of line height)
                if abs(line["y"] - last_line["y"]) < (h_ref * 0.6):
                    last_row.append(line)
                else:
                    rows.append([line])
                    
        # Sort each row horizontally (left-to-right)
        for row in rows:
            row.sort(key=lambda l: l["x"])
            
        # 3. Format as Markdown structures
        markdown_blocks = []
        in_table = False
        table_rows = []
        
        for row in rows:
            is_table_row = len(row) >= 2
            
            if is_table_row:
                in_table = True
                row_str = "| " + " | ".join([item["text"] for item in row]) + " |"
                table_rows.append(row_str)
            else:
                if in_table and table_rows:
                    markdown_blocks.append(self._format_markdown_table(table_rows))
                    table_rows = []
                    in_table = False
                    
                line_item = row[0]
                text = line_item["text"]
                is_header = False
                text_clean = text.strip().upper()
                if text_clean in [
                    "AGREEMENT OF SALE", "SCHEDULE A", "SCHEDULE B", "WORK ORDER", 
                    "RECEIPT", "NOC", "BUILDING PERMIT ORDER", "SPECIAL CONDITIONS", 
                    "ADDITIONAL CONDITIONS"
                ]:
                    is_header = True
                elif len(text) < 40 and text_clean.startswith("SCHEDULE"):
                    is_header = True
                    
                if is_header:
                    markdown_blocks.append(f"\n## {text}\n")
                else:
                    markdown_blocks.append(text)
                    
        # Output any trailing table rows
        if in_table and table_rows:
            markdown_blocks.append(self._format_markdown_table(table_rows))
            
        return "\n".join(markdown_blocks)
        
    def _format_markdown_table(self, table_rows: list[str]) -> str:
        if not table_rows:
            return ""
        max_cols = 0
        for r in table_rows:
            cols = r.count("|") - 1
            if cols > max_cols:
                max_cols = cols
                
        divider = "| " + " | ".join(["---"] * max_cols) + " |"
        result = [table_rows[0], divider]
        result.extend(table_rows[1:])
        return "\n" + "\n".join(result) + "\n"
