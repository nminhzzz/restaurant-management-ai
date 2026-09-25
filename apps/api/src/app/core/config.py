"""Application settings, loaded from the environment (see `.env.example`)."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[5]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", Path(".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = Field(default=["http://localhost:3000"])

    database_url: str = (
        "mysql+asyncmy://restaurant:restaurant@localhost:3306/restaurant?charset=utf8mb4"
    )

    jwt_secret: str = "dev-only-secret-replace-me-0123456789"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 480

    # AI Assistant (NFR-02 response budget, NFR-16 cost control).
    ai_provider: str = "openai"
    ai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_base_url: str = ""
    ai_ollama_base_url: str = "http://localhost:11434"
    ai_max_rows: int = 500
    ai_response_budget_seconds: float = 8.0
    ai_daily_question_quota: int = 500

    # NFR-06 execution limits: a query runs at most `ai_sql_timeout_seconds` on the
    # database, and the model gets at most `ai_max_sql_attempts` tries per question.
    ai_sql_timeout_seconds: float = 3.0
    ai_max_sql_attempts: int = 2

    payment_webhook_secret: str = ""

    # NFR-06 requires one read-only account per role, each granted SELECT on that
    # role's view only — never a single account shared by all three roles.
    ai_readonly_url_manager: str = ""
    ai_readonly_url_cashier: str = ""
    ai_readonly_url_warehouse: str = ""


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    if (
        settings.environment != "local"
        and settings.jwt_secret == "dev-only-secret-replace-me-0123456789"
    ):
        raise RuntimeError(
            "JWT_SECRET must be set via env when ENVIRONMENT != local "
            "(refusing to run with default dev secret)"
        )
    if settings.environment != "local" and not settings.payment_webhook_secret:
        raise RuntimeError("PAYMENT_WEBHOOK_SECRET must be set when ENVIRONMENT != local")
    return settings
