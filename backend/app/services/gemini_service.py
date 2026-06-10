from __future__ import annotations

import json
import os
from typing import Any

try:
    import google.generativeai as genai
except ImportError:
    genai = None


class GeminiService:
    def __init__(self) -> None:
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and genai is not None:
            genai.configure(api_key=api_key)

    def extract_field_with_gemini(
        self,
        *,
        field_code: str,
        label: str,
        keywords: list[str],
        text_chunk: str,
    ) -> dict[str, Any]:
        """
        Queries Gemini API to extract a specific field based on custom prompt structure
        and returns the extracted value with default AI confidence.
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or genai is None:
            return {"value": None, "confidence": 0.0}

        keywords_str = "\n".join(keywords) if keywords else label
        prompt = f"""Extract {field_code} from the following text.
Field Description / Label: {label}

Possible keywords/context clues:
{keywords_str}

Return ONLY a valid JSON object matching this schema, without any backticks, markdown formatting, or explanation:
{{
  "{field_code}": "extracted value or null"
}}

Document text:
{text_chunk}
"""
        try:
            model = genai.GenerativeModel(self.model_name)
            # Fetch content. Attempting JSON schema mode
            response = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            raw_response = response.text.strip()
            data = json.loads(raw_response)
            val = data.get(field_code)
            if val and str(val).lower() != "null":
                return {"value": str(val), "confidence": 0.85}
        except Exception:
            # Fallback text cleaner if JSON response includes markdown wrapper block
            try:
                text = response.text.strip()
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                data = json.loads(text)
                val = data.get(field_code)
                if val and str(val).lower() != "null":
                    return {"value": str(val), "confidence": 0.85}
            except Exception:
                pass

        return {"value": None, "confidence": 0.0}

    def fallback_low_confidence_fields(
        self,
        fields: dict[str, dict[str, Any]],
        full_text: str,
    ) -> dict[str, dict[str, Any]]:
        """
        Runs selective LLM fallback for fields with confidence < 0.90
        """
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or genai is None:
            return fields

        for field_code, data in fields.items():
            if field_code == "confidence":
                continue
            
            if data.get("final_confidence", 0.0) < 0.90:
                label = field_code.replace("_", " ").title()
                text_chunk = full_text[:8000]
                
                ai_res = self.extract_field_with_gemini(
                    field_code=field_code,
                    label=label,
                    keywords=[],
                    text_chunk=text_chunk
                )
                
                if ai_res and ai_res.get("value"):
                    data["value"] = ai_res["value"]
                    data["ocr_confidence"] = 0.90
                    data["regex_confidence"] = 0.90
                    data["final_confidence"] = 0.90
                    if not data.get("source_page"):
                        data["source_page"] = 1
                        
        return fields
