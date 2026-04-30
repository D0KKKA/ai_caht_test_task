"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """App configuration loaded from environment variables."""

    # API Keys & URLs
    openrouter_api_key: str
    openrouter_api_url: str = "https://openrouter.ai/api/v1/chat/completions"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:1234@localhost:5432/ai_chat_db"

    # LLM Model
    model_name: str = "google/gemma-3-27b-it:free"

    # Context Management Thresholds
    message_threshold: int = 30  # Trigger summarization when exceeded
    recent_messages_kept: int = 20  # Always send last N messages to LLM
    summary_batch_size: int = 10  # How many old messages to summarize per run

    # System Prompts
    system_prompt: str = (
        "You are a helpful AI assistant. "
        "Provide clear, concise, and accurate answers. "
        "Use markdown formatting when appropriate."
    )

    summarization_prompt: str = (
        "Summarize the following conversation segment concisely, "
        "preserving key facts and context. Keep it under 150 words."
    )

    title_generation_prompt: str = (
        "Generate a concise 3-5 word title for a conversation based on the first message. "
        "Reply with ONLY the title, no quotes, no punctuation."
    )

    model_config = {
        "protected_namespaces": ("settings_",),
        "env_file": ".env",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
