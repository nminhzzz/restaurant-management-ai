"""Application settings, loaded from the environment (see `.env.example`)."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", Path(".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default=["http://localhost:3000"])

    database_url: str = "postgresql+psycopg://restaurant:restaurant@localhost:5432/restaurant"

    jwt_secret: str = "dev-only-secret-replace-me-in-dotenv-0123456789"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 480

    # AI Assistant (NFR-02 response budget, NFR-16 cost control).
    ai_provider: str = "openai"
    ai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_ollama_base_url: str = "http://localhost:11434"
    ai_max_rows: int = 500
    ai_timeout_seconds: float = 8.0
    ai_daily_question_quota: int = 500


@lru_cache
def get_settings() -> Settings:
    return Settings()
