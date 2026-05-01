"""Application configuration using Pydantic Settings."""

from functools import lru_cache
import json
from typing import Annotated, Any
from urllib.parse import quote

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode


def build_postgres_url(
    *,
    host: str,
    port: int,
    database: str,
    user: str,
    password: str,
    driver: str,
) -> str:
    """Build a PostgreSQL DSN from discrete connection parameters."""
    quoted_user = quote(user, safe="")
    quoted_password = quote(password, safe="")
    quoted_database = quote(database, safe="")

    return (
        f"postgresql+{driver}://{quoted_user}:{quoted_password}"
        f"@{host}:{port}/{quoted_database}"
    )


class Settings(BaseSettings):
    """App configuration loaded from environment variables."""

    # API Keys & URLs
    openrouter_api_key: str
    openrouter_api_url: str = "https://openrouter.ai/api/v1/chat/completions"

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "ai_chat_db"
    postgres_user: str = "postgres"
    postgres_password: str = "1234"

    # CORS — comma-separated list of allowed origins (e.g. "http://localhost:3000,https://yourdomain.com")
    allowed_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Rate limiting
    rate_limit: str = "60/minute"

    # LLM Model
    model_name: str = "openai/gpt-oss-20b:free"

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
        "extra": "ignore",
    }

    @property
    def database_url(self) -> str:
        """Async SQLAlchemy database URL."""
        return build_postgres_url(
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
            user=self.postgres_user,
            password=self.postgres_password,
            driver="asyncpg",
        )

    @property
    def alembic_database_url(self) -> str:
        """Sync database URL for Alembic migrations."""
        return build_postgres_url(
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
            user=self.postgres_user,
            password=self.postgres_password,
            driver="psycopg2",
        )

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
