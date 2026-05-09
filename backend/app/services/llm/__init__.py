"""
LLM provider factory.

Import `get_provider()` anywhere you need to call an LLM. It reads
LLM_PROVIDER from settings and returns the appropriate provider instance,
already configured with the correct API key / model / base URL.

Usage:
    from app.services.llm import get_provider

    provider = get_provider()
    response = provider.generate(prompt="...", context=["chunk1", "chunk2"])

The returned object always satisfies the BaseLLMProvider protocol, so
callers don't need to know which concrete class they got.
"""

from app.core.config import settings
from app.services.llm.base import BaseLLMProvider, Citation, LLMResponse


def get_provider() -> BaseLLMProvider:
    """
    Instantiate and return the LLM provider configured in settings.

    Raises ValueError for unknown provider names so misconfiguration is
    caught at call time with a clear message rather than an AttributeError
    deep in a provider class.
    """
    provider_name = settings.llm_provider.lower()

    if provider_name == "ollama":
        from app.services.llm.ollama import OllamaProvider
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )

    if provider_name == "gemini":
        from app.services.llm.gemini import GeminiProvider
        return GeminiProvider(api_key=settings.gemini_api_key)

    if provider_name == "claude":
        from app.services.llm.claude import ClaudeProvider
        return ClaudeProvider(api_key=settings.claude_api_key)

    if provider_name == "openai":
        from app.services.llm.openai import OpenAIProvider
        return OpenAIProvider(api_key=settings.openai_api_key)

    raise ValueError(
        f"Unknown LLM provider: '{provider_name}'. "
        "Set LLM_PROVIDER to one of: ollama, gemini, claude, openai"
    )


__all__ = ["get_provider", "BaseLLMProvider", "LLMResponse", "Citation"]
