from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the .env path relative to this file, not the working directory.
# This means `uv run alembic ...` and `uv run uvicorn ...` both find .env
# regardless of which directory they're run from.
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or a .env file.

    Think of this like Vite's `import.meta.env` — it reads from .env
    during development and from real environment variables in production.
    Pydantic validates types automatically, so DATABASE_URL can't be
    accidentally set to a number.
    """

    app_name: str = "Relativity Clone API"
    debug: bool = False

    # PostgreSQL connection string — set this in your .env file
    database_url: str = "postgresql://localhost/relativity"

    # Comma-separated list of allowed frontend origins for CORS.
    # Stored as a plain string in .env and split at runtime to avoid JSON
    # parsing issues with list values in .env files.
    cors_origins_str: str = "http://localhost:9000"

    # ── LLM provider settings ──────────────────────────────────────────────────
    # Which provider to use: "ollama", "gemini", "claude", "openai"
    llm_provider: str = "ollama"

    # Ollama — runs locally, no API key needed.
    # Default model is llama3.2 (3B, fast) but any model pulled via `ollama pull`
    # works. The base URL matches Ollama's default local server port.
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"

    # API keys for cloud providers — leave blank if not using that provider.
    gemini_api_key: str = ""
    claude_api_key: str = ""
    openai_api_key: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_str.split(",")]

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
    )


# Single shared instance — import this everywhere instead of re-instantiating
settings = Settings()
