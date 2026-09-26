"""Application settings, loaded from the environment (see `.env.example`)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

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
    # DeepSeek's OpenAI-compatible API is the default commercial provider.
    ai_provider: str = "deepseek"
    ai_api_key: str = ""
    llm_model: str = "deepseek-flash"
    llm_base_url: str = ""
    # Runtime fallback (report §1.4.2, §4.1.1): used only when the primary model call
    # fails (transport error, timeout, 429 or 5xx); empty falls back to `ai_config_c_model`.
    llm_fallback_model: str = ""
    # DeepSeek thinks at "high" by default; two LLM calls per question then overrun
    # the 8s budget (NFR-02). Only sent when AI_PROVIDER=deepseek; empty = send nothing.
    llm_reasoning_effort: str = "low"
    # Configuration C of the A/B/C experiment runs configuration B on a second model
    # (master-roadmap Q5); empty means the harness falls back to a suffixed name.
    ai_config_c_model: str = ""
    ai_ollama_base_url: str = "http://localhost:11434"
    ai_max_rows: int = 500
    ai_response_budget_seconds: float = 8.0
    ai_daily_question_quota: int = 500

    # NFR-06 execution limits: a query runs at most `ai_sql_timeout_seconds` on the
    # database, and the model gets at most `ai_max_sql_attempts` tries per question.
    ai_sql_timeout_seconds: float = 3.0
    ai_max_sql_attempts: int = 2

    payment_webhook_secret: str = ""

    # PAYMENT_GATEWAY picks the QR adapter; the simulator stays the default for tests.
    payment_gateway: Literal["simulator", "sepay"] = "simulator"
    sepay_bank_account: str = ""
    sepay_bank_code: str = ""
    sepay_account_name: str = ""
    sepay_webhook_api_key: str = ""
    sepay_api_token: str = ""
    sepay_payment_prefix: str = "TT"
    sepay_api_url: str = "https://my.sepay.vn/userapi"

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
    if settings.payment_gateway == "sepay" and not (
        settings.sepay_bank_account and settings.sepay_bank_code and settings.sepay_webhook_api_key
    ):
        raise RuntimeError(
            "SEPAY_BANK_ACCOUNT, SEPAY_BANK_CODE and SEPAY_WEBHOOK_API_KEY must be set "
            "when PAYMENT_GATEWAY=sepay"
        )
    return settings
