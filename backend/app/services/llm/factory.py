import os
from backend.app.services.llm.mock_provider import MockLLMProvider, UnavailableLLMProvider
from backend.app.services.app_settings import load_settings

def get_llm_provider():
    settings = load_settings()
    provider = (settings.ai.active_provider or "mock").lower()
    openai_key = (
        settings.ai.openai_api_key
        or os.getenv("OPENAI_API_KEY", "")
        or os.getenv("OPENROUTER_API_KEY", "")
    )
    gemini_key = settings.ai.gemini_api_key or os.getenv("GEMINI_API_KEY", "")

    if provider == "mock":
        return MockLLMProvider()

    if provider in ("openai", "auto") and openai_key and openai_key != "mock":
        from backend.app.services.llm.openai_provider import OpenAIProvider
        return OpenAIProvider(openai_key, settings.ai.openai_model)

    if provider in ("gemini", "auto") and gemini_key:
        from backend.app.services.llm.gemini_provider import GeminiLLMProvider
        return GeminiLLMProvider(gemini_key, settings.ai.gemini_model)

    return UnavailableLLMProvider("Real AI key needed. Add an OpenAI or Gemini key in Settings, or switch to Demo Mode.")
