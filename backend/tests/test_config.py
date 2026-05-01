"""Tests for environment-driven application settings."""

import unittest

from app.core.config import Settings, build_postgres_url


class ConfigTests(unittest.TestCase):
    def test_build_postgres_url_from_discrete_values(self):
        url = build_postgres_url(
            host="db",
            port=5432,
            database="ai_chat_db",
            user="chat_user",
            password="pa:ss word",
            driver="asyncpg",
        )

        self.assertEqual(
            url,
            "postgresql+asyncpg://chat_user:pa%3Ass%20word@db:5432/ai_chat_db",
        )

    def test_settings_expose_async_and_alembic_urls(self):
        settings = Settings(
            openrouter_api_key="test-key",
            postgres_host="postgres",
            postgres_port=5432,
            postgres_db="ai_chat_db",
            postgres_user="postgres",
            postgres_password="1234",
        )

        self.assertEqual(
            settings.database_url,
            "postgresql+asyncpg://postgres:1234@postgres:5432/ai_chat_db",
        )
        self.assertEqual(
            settings.alembic_database_url,
            "postgresql+psycopg2://postgres:1234@postgres:5432/ai_chat_db",
        )


if __name__ == "__main__":
    unittest.main()
