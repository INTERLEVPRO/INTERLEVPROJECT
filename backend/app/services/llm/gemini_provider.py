import google.generativeai as genai
import json
import os
from typing import Dict, Any, Optional
from backend.app.services.llm.base import LLMProvider

class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    def extract_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Uses Gemini to extract structured data."""
        # We append a instruction to ensure JSON output
        full_prompt = f"{prompt}\n\nPlease respond ONLY with a valid JSON object. No extra text."
        
        response = self.model.generate_content(full_prompt)
        text = response.text
        
        # Simple extraction logic (finding first { and last })
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = text[start:end]
                return json.loads(json_str)
            return {"error": "Could not find JSON in response", "raw": text}
        except Exception as e:
            return {"error": str(e), "raw": text}

    def generate_text(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text

    def summarize(self, text: str) -> str:
        prompt = f"Summarize the following text professionally:\n\n{text}"
        return self.generate_text(prompt)
