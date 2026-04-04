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

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_str.split(",")]

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
    )


# Single shared instance — import this everywhere instead of re-instantiating
settings = Settings()
