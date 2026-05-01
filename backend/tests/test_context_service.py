"""Focused tests for long-chat context handling."""

from types import SimpleNamespace
import unittest

from app.services.context_service import ContextService


class FakeChatRepository:
    """Minimal async chat repository stub."""

    def __init__(self, chat):
        self.chat = chat
        self.updated_summary = None
        self.db = None

    async def get_by_id(self, chat_id):
        return self.chat

    async def update(self, chat_id, *, summary, commit=True):
        self.updated_summary = summary
        self.chat.summary = summary
        return self.chat


class FakeMessageRepository:
    """Minimal async message repository stub."""

    def __init__(self, messages, count):
        self.messages = messages
        self.count = count
        self.requested_recent_limit = None
        self.requested_oldest_limit = None
        self.marked_ids = None
        self.db = None

    async def get_recent_unsummarized(self, chat_id, limit):
        self.requested_recent_limit = limit
        return self.messages[-limit:]

    async def count_unsummarized(self, chat_id):
        return self.count

    async def get_oldest_unsummarized(self, chat_id, limit):
        self.requested_oldest_limit = limit
        return self.messages[:limit]

    async def mark_as_summarized(self, message_ids, *, commit=True):
        self.marked_ids = message_ids
        return len(message_ids)


class FakeLLMService:
    """Minimal async LLM stub."""

    def __init__(self, response):
        self.response = response
        self.calls = 0

    async def completion(self, messages, temperature):
        self.calls += 1
        return self.response


class FakeDB:
    """Track commit/rollback behaviour."""

    def __init__(self):
        self.commit_calls = 0
        self.rollback_calls = 0

    async def commit(self):
        self.commit_calls += 1

    async def rollback(self):
        self.rollback_calls += 1


class ContextServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_build_context_uses_threshold_sized_active_window(self):
        chat = SimpleNamespace(summary="Earlier summary")
        messages = [
            SimpleNamespace(role="user", content=f"message {idx}")
            for idx in range(25)
        ]
        chat_repo = FakeChatRepository(chat)
        message_repo = FakeMessageRepository(messages, count=len(messages))
        service = ContextService(chat_repo, message_repo, FakeLLMService("unused"))
        service.settings.recent_messages_kept = 20
        service.settings.message_threshold = 30

        context = await service.build_context("chat-1", FakeDB())

        self.assertEqual(message_repo.requested_recent_limit, 30)
        self.assertEqual(context[0]["role"], "system")
        self.assertEqual(context[1]["content"], "[Previous context summary]:\nEarlier summary")
        self.assertEqual(len(context), 27)

    async def test_maybe_summarize_only_fetches_oldest_batch_and_commits_once(self):
        chat = SimpleNamespace(summary=None)
        messages = [
            SimpleNamespace(id=f"msg-{idx}", role="user", content=f"message {idx}")
            for idx in range(15)
        ]
        chat_repo = FakeChatRepository(chat)
        message_repo = FakeMessageRepository(messages, count=31)
        llm = FakeLLMService("compressed summary")
        db = FakeDB()
        service = ContextService(chat_repo, message_repo, llm)
        service.settings.message_threshold = 30
        service.settings.summary_batch_size = 10

        await service.maybe_summarize("chat-1", db)

        self.assertEqual(message_repo.requested_oldest_limit, 10)
        self.assertEqual(message_repo.marked_ids, [f"msg-{idx}" for idx in range(10)])
        self.assertEqual(chat_repo.updated_summary, "compressed summary")
        self.assertEqual(llm.calls, 1)
        self.assertEqual(db.commit_calls, 1)
        self.assertEqual(db.rollback_calls, 0)


if __name__ == "__main__":
    unittest.main()
