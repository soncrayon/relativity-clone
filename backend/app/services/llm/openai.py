"""
OpenAI LLM provider (stub).

Requires: OPENAI_API_KEY in .env and LLM_PROVIDER=openai.

Install the SDK when implementing:
  uv add openai

See ADR 0003 for the provider interface contract.
"""

from app.services.llm.base import LLMResponse


class OpenAIProvider:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, context: list[str]) -> LLMResponse:
        raise NotImplementedError(
            "OpenAIProvider is not yet implemented. "
            "Set LLM_PROVIDER=ollama in .env to use the local Ollama provider instead, "
            "or implement this provider using the openai SDK."
        )
