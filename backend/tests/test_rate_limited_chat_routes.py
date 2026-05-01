"""Regression tests for rate-limited chat routes."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import unittest
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1 import chats as chats_module
from app.core.database import get_db
from app.core.dependencies import get_client_id
from app.core.rate_limit import limiter


TEST_CLIENT_ID = UUID("11111111-1111-1111-1111-111111111111")


async def override_get_db():
    """Return a dummy DB session object."""
    yield object()


async def override_get_client_id():
    """Return a stable anonymous client ID for tests."""
    return TEST_CLIENT_ID


def build_test_app() -> FastAPI:
    """Build a small app containing only the chat routes."""
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.include_router(chats_module.router)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_client_id] = override_get_client_id
    return app


class RateLimitedChatRoutesTests(unittest.TestCase):
    def test_create_chat_with_rate_limit_headers_returns_201(self):
        chat = SimpleNamespace(
            id=UUID("22222222-2222-2222-2222-222222222222"),
            client_id=TEST_CLIENT_ID,
            title=None,
            created_at=datetime(2026, 5, 1, 12, 0, 0),
            updated_at=datetime(2026, 5, 1, 12, 0, 0),
            message_count=0,
        )
        chat_service = SimpleNamespace(create_chat=AsyncMock(return_value=chat))

        app = build_test_app()
        with patch.object(chats_module, "get_chat_repository", AsyncMock(return_value=object())), patch.object(
            chats_module,
            "get_chat_service",
            AsyncMock(return_value=chat_service),
        ), patch.object(chats_module, "get_llm_service", return_value=object()):
            client = TestClient(app)
            response = client.post(
                "/chats",
                headers={"X-Client-Id": str(TEST_CLIENT_ID)},
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["id"], str(chat.id))
        self.assertIn("X-RateLimit-Limit", response.headers)

    def test_delete_chat_with_rate_limit_headers_returns_204(self):
        chat_service = SimpleNamespace(delete_chat=AsyncMock(return_value=True))

        app = build_test_app()
        with patch.object(chats_module, "get_chat_repository", AsyncMock(return_value=object())), patch.object(
            chats_module,
            "get_chat_service",
            AsyncMock(return_value=chat_service),
        ), patch.object(chats_module, "get_llm_service", return_value=object()):
            client = TestClient(app)
            response = client.delete(
                "/chats/33333333-3333-3333-3333-333333333333",
                headers={"X-Client-Id": str(TEST_CLIENT_ID)},
            )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertIn("X-RateLimit-Limit", response.headers)


if __name__ == "__main__":
    unittest.main()
