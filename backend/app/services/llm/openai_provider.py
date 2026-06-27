from openai import OpenAI
import json
import os
from typing import Dict, Any, Optional
from backend.app.services.llm.base import LLMProvider

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        client_kwargs: Dict[str, Any] = {"api_key": api_key}
        is_openrouter = api_key.startswith("sk-or-v1-")
        if is_openrouter:
            # OpenRouter keys use the OpenAI-compatible API with a different base URL.
            client_kwargs["base_url"] = "https://openrouter.ai/api/v1"
            client_kwargs["default_headers"] = {
                "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://interlev.ai"),
                "X-Title": os.getenv("OPENROUTER_APP_NAME", "INTERLEV AI"),
            }
            if not model.startswith("openai/"):
                model = f"openai/{model}"
        else:
            if model.startswith("openai/"):
                model = model.split("/", 1)[1]
        self.client = OpenAI(**client_kwargs)
        self.model = model

    def extract_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=1000,
            temperature=0.1,
        )
        return json.loads(response.choices[0].message.content)

    def generate_text(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.2,
        )
        return response.choices[0].message.content

    def summarize(self, text: str) -> str:
        return self.generate_text(f"Summarize: {text}")
