"""
Anthropic Claude LLM provider (stub).

Requires: CLAUDE_API_KEY in .env and LLM_PROVIDER=claude.

Install the SDK when implementing:
  uv add anthropic

See ADR 0003 for the provider interface contract.
"""

from app.services.llm.base import LLMResponse


class ClaudeProvider:
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-latest") -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str, context: list[str]) -> LLMResponse:
        raise NotImplementedError(
            "ClaudeProvider is not yet implemented. "
            "Set LLM_PROVIDER=ollama in .env to use the local Ollama provider instead, "
            "or implement this provider using the anthropic SDK."
        )
