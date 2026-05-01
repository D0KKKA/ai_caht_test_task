"""Application configuration using Pydantic Settings."""

from functools import lru_cache
import json
from typing import Annotated, Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode


class Settings(BaseSettings):
    """App configuration loaded from environment variables."""

    # API Keys & URLs
    openrouter_api_key: str
    openrouter_api_url: str = "https://openrouter.ai/api/v1/chat/completions"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:1234@localhost:5432/ai_chat_db"

    # CORS — comma-separated list of allowed origins (e.g. "http://localhost:3000,https://yourdomain.com")
    allowed_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Rate limiting
    rate_limit: str = "60/minute"

    # LLM Model
    model_name: str = "google/gemma-3-27b-it:free"

    # Database connection pool (ops-tunable)
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_command_timeout: int = 30  # seconds

    # HTTP client timeout for LLM requests (ops-tunable)
    llm_request_timeout: float = 60.0  # seconds

    # Context Management Thresholds
    message_threshold: int = 30  # Trigger summarization when exceeded
    recent_messages_kept: int = 20  # Always send last N messages to LLM
    summary_batch_size: int = 10  # How many old messages to summarize per run

    model_config = {
        "protected_namespaces": ("settings_",),
        "env_file": ".env",
        "case_sensitive": False,
    }

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Any) -> Any:
        """Accept either JSON arrays or comma-separated origin strings."""
        if value is None:
            return value

        if isinstance(value, (list, tuple, set)):
            return [str(origin).strip() for origin in value if str(origin).strip()]

        if isinstance(value, str):
            raw_value = value.strip()
            if not raw_value:
                return []

            if raw_value.startswith("["):
                parsed_value = json.loads(raw_value)
                if not isinstance(parsed_value, list):
                    raise ValueError("ALLOWED_ORIGINS JSON value must be a list")

                return [
                    str(origin).strip()
                    for origin in parsed_value
                    if str(origin).strip()
                ]

            return [
                origin.strip()
                for origin in raw_value.split(",")
                if origin.strip()
            ]

        raise TypeError("allowed_origins must be a list or comma-separated string")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
