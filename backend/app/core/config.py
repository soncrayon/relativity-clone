from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Which frontend origins are allowed to call this API.
    # FastAPI's CORS middleware rejects requests from any origin not in this list.
    cors_origins: list[str] = ["http://localhost:9000"]

    model_config = SettingsConfigDict(
        # Load .env from the backend/ directory (one level up from app/)
        env_file="../.env",
        env_file_encoding="utf-8",
    )


# Single shared instance — import this everywhere instead of re-instantiating
settings = Settings()
