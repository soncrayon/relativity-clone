"""
Google Gemini LLM provider (stub).

Requires: GEMINI_API_KEY in .env and LLM_PROVIDER=gemini.

Install the SDK when implementing:
  uv add google-genai

See ADR 0003 for the provider interface contract.
"""

from app.services.llm.base import LLMResponse


class GeminiProvider:
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash") -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, context: list[str]) -> LLMResponse:
        raise NotImplementedError(
            "GeminiProvider is not yet implemented. "
            "Set LLM_PROVIDER=ollama in .env to use the local Ollama provider instead, "
            "or implement this provider using the google-genai SDK."
        )
