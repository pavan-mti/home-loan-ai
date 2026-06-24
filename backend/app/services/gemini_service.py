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
        print("GEMINI_API_KEY FOUND:", bool(os.getenv("GEMINI_API_KEY")))
        print("OPENAI_API_KEY FOUND:", bool(os.getenv("OPENAI_API_KEY")))

        if not os.getenv("GEMINI_API_KEY") and not os.getenv("OPENAI_API_KEY"):
            from pathlib import Path
            from dotenv import load_dotenv
            
            root_dir = Path(__file__).resolve().parents[2]
            env_path1 = root_dir / ".env"
            env_path2 = root_dir.parent / ".env"
            
            print("ENV PATH:", env_path1)
            load_dotenv(env_path1, override=True)
            print("ENV PATH:", env_path2)
            load_dotenv(env_path2, override=True)
            
            print("GEMINI_API_KEY FOUND:", bool(os.getenv("GEMINI_API_KEY")))
            print("OPENAI_API_KEY FOUND:", bool(os.getenv("OPENAI_API_KEY")))

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
        
        keywords_str = ", ".join(keywords) if keywords else label
        prompt = f"""You are an expert information extraction assistant specialized in analyzing Indian legal, property, and valuation documents.
Your task is to extract the value for a specific field from the provided document text.

Field Code: {field_code}
Field Label: {label}
Potential aliases or keywords to look for: {keywords_str}

STRICT INSTRUCTIONS:
1. Examine the document text carefully and locate the information corresponding to this field.
2. Return ONLY a valid JSON object matching the exact schema below, without any markdown formatting, backticks, or explanation.
3. If the value is missing, not mentioned, or not found in the text, you must return null for the field value. Do NOT guess or invent information.
4. Keep the output strictly in this JSON format:
{{
  "{field_code}": "extracted value or null"
}}

Document text:
{text_chunk}
"""

        # 1. Try Gemini if key is present
        if gemini_key and genai is not None:
            response = None
            try:
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content(
                    prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                print("========== GEMINI ==========")
                print("FIELD:", field_code)
                print(response.text)
                print("============================")
                raw_response = response.text.strip()
                data = json.loads(raw_response)
                val = data.get(field_code)
                if val and str(val).lower() != "null":
                    return {"value": str(val), "confidence": 0.85}
            except Exception as e:
                print("Gemini error:", e)
                if response is not None:
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
                    except Exception as inner_e:
                        print("Gemini error:", inner_e)

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
            except Exception as e:
                print("OpenAI error:", e)

        return {"value": None, "confidence": 0.0}

    def fallback_low_confidence_fields(
        self,
        fields: dict[str, dict[str, Any]],
        full_text: str,
        required_fields: list[str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        Runs selective LLM fallback for fields with confidence < 0.90
        """
        print("Inside fallback_low_confidence_fields")
        print("GEMINI KEY =", bool(os.getenv("GEMINI_API_KEY")))
        print("OPENAI KEY =", bool(os.getenv("OPENAI_API_KEY")))
        print("GEMINI_API_KEY FOUND:", bool(os.getenv("GEMINI_API_KEY")))
        print("OPENAI_API_KEY FOUND:", bool(os.getenv("OPENAI_API_KEY")))
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        if not gemini_key and not openai_key:
            return fields

        try:
            from .extractors.base import FIELD_LABELS
        except Exception:
            FIELD_LABELS = {}

        for field_code, data in fields.items():
            if field_code == "confidence":
                continue
            
            if required_fields is not None and field_code not in required_fields:
                continue

            if data.get("final_confidence", 0.0) < 0.90:
                print(f"Gemini fallback called for: {field_code}")
                labels = FIELD_LABELS.get(field_code, [])
                label = labels[0] if labels else field_code.replace("_", " ").title()
                text_chunk = full_text[:12000]
                
                ai_res = self.extract_field_with_llm(
                    field_code=field_code,
                    label=label,
                    keywords=labels,
                    text_chunk=text_chunk
                )
                print("====================")
                print("FIELD:", field_code)
                print("LABEL:", label)
                print("KEYWORDS:", labels)
                print("AI RESPONSE:", ai_res)
                print("====================")
                
                if ai_res and ai_res.get("value"):
                    data["value"] = ai_res["value"]
                    data["ocr_confidence"] = 0.90
                    data["regex_confidence"] = 0.90
                    data["final_confidence"] = 0.90
                    if not data.get("source_page"):
                        data["source_page"] = 1
                        
        return fields