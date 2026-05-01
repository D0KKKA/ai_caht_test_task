"""Context service for managing message context and summarization."""

import json
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import (
    TEMPERATURE_SUMMARIZATION,
    MAX_SUMMARY_LENGTH,
    SUMMARY_CONTEXT_LABEL,
    SUMMARY_LATER_LABEL,
)
from app.core.prompts import SUMMARIZER_ROLE_PROMPT, SYSTEM_PROMPT, SUMMARIZATION_PROMPT
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ContextService:
    """Service for building and managing LLM context."""

    def __init__(
        self,
        chat_repo: ChatRepository,
        message_repo: MessageRepository,
        llm_service: LLMService,
    ):
        """Initialize context service with dependencies."""
        self.chat_repo = chat_repo
        self.message_repo = message_repo
        self.llm_service = llm_service
        self.settings = get_settings()

    async def build_context(self, chat_id: UUID, db: AsyncSession) -> list[dict]:
        """Build the messages list to send to LLM.

        Strategy:
        1. Load chat summary (accumulated from old messages)
        2. Get recent unsummarized messages (last N)
        3. Construct: [system] + [summary_message if exists] + [recent_messages]
        """
        self.chat_repo.db = db
        self.message_repo.db = db

        chat = await self.chat_repo.get_by_id(chat_id)
        if not chat:
            raise ValueError(f"Chat {chat_id} not found")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]

        if chat.summary:
            messages.append(
                {
                    "role": "assistant",
                    "content": f"{SUMMARY_CONTEXT_LABEL}{chat.summary}",
                }
            )

        recent_messages = await self.message_repo.get_recent_unsummarized(
            chat_id, limit=self.settings.recent_messages_kept
        )

        for msg in recent_messages:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    async def maybe_summarize(self, chat_id: UUID, db: AsyncSession) -> None:
        """Check if messages should be summarized and perform if needed.

        Triggered after each message is added. Summarizes oldest batch when
        unsummarized message count exceeds threshold.
        """
        self.chat_repo.db = db
        self.message_repo.db = db

        # Fetch all unsummarized in one query (avoids extra COUNT query)
        all_unsummarized = await self.message_repo.get_unsummarized_by_chat(chat_id)

        if len(all_unsummarized) <= self.settings.message_threshold:
            return

        batch_to_summarize = all_unsummarized[: self.settings.summary_batch_size]

        if not batch_to_summarize:
            return

        # Use JSON to safely encode user content — prevents prompt injection
        formatted_messages = json.dumps(
            [{"role": msg.role, "content": msg.content} for msg in batch_to_summarize],
            ensure_ascii=False,
            indent=2,
        )

        summary_prompt = (
            f"{SUMMARIZATION_PROMPT}\n\n"
            f"Conversation (JSON format):\n{formatted_messages}"
        )

        try:
            new_summary = await self.llm_service.completion(
                [
                    {"role": "system", "content": SUMMARIZER_ROLE_PROMPT},
                    {"role": "user", "content": summary_prompt},
                ],
                temperature=TEMPERATURE_SUMMARIZATION,
            )
        except Exception as e:
            logger.error("Summarization failed for chat %s: %s", chat_id, e)
            return

        chat = await self.chat_repo.get_by_id(chat_id)
        if not chat:
            return

        if chat.summary:
            combined_summary = f"{chat.summary}{SUMMARY_LATER_LABEL}{new_summary}"
        else:
            combined_summary = new_summary

        # Keep the beginning of the summary (most established context), not the end
        if len(combined_summary) > MAX_SUMMARY_LENGTH:
            combined_summary = combined_summary[:MAX_SUMMARY_LENGTH]

        await self.chat_repo.update(chat_id, summary=combined_summary)

        message_ids = [msg.id for msg in batch_to_summarize]
        await self.message_repo.mark_as_summarized(message_ids)
