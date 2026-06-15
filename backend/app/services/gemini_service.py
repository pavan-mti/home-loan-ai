from __future__ import annotations

import json
import os
from typing import Any

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class GeminiService:
    def __init__(self) -> None:
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and genai is not None:
            genai.configure(api_key=api_key)

    def extract_field_with_llm(
        self,
        *,
        field_code: str,
        label: str,
        keywords: list[str],
        text_chunk: str,
    ) -> dict[str, Any]:
        """
        Queries Gemini or OpenAI to extract a specific field based on custom prompt structure
        and returns the extracted value with default AI confidence.
        """
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
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

        # 1. Try Gemini if key is present
        if gemini_key and genai is not None:
            try:
                model = genai.GenerativeModel(self.model_name)
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

        # 2. Try OpenAI if key is present and Gemini failed or was skipped
        if openai_key and OpenAI is not None:
            try:
                client = OpenAI(api_key=openai_key)
                response = client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that extracts data in JSON format."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                raw_response = response.choices[0].message.content.strip()
                data = json.loads(raw_response)
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
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        if not gemini_key and not openai_key:
            return fields

        for field_code, data in fields.items():
            if field_code == "confidence":
                continue
            
            if data.get("final_confidence", 0.0) < 0.90:
                label = field_code.replace("_", " ").title()
                text_chunk = full_text[:8000]
                
                ai_res = self.extract_field_with_llm(
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
