"""Context service for managing message context and summarization."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.services.llm_service import LLMService


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

        Args:
            chat_id: ID of the chat
            db: Database session

        Returns:
            List of message dicts with role and content keys
        """
        # Set repository session
        self.chat_repo.db = db
        self.message_repo.db = db

        # Load chat to get summary
        chat = await self.chat_repo.get_by_id(chat_id)
        if not chat:
            raise ValueError(f"Chat {chat_id} not found")

        # Build message context
        messages = [
            {"role": "system", "content": self.settings.system_prompt},
        ]

        # Add summary as assistant message if it exists
        if chat.summary:
            messages.append(
                {
                    "role": "assistant",
                    "content": f"[Previous context summary]:\n{chat.summary}",
                }
            )

        # Get recent unsummarized messages
        recent_messages = await self.message_repo.get_recent_unsummarized(
            chat_id, limit=self.settings.recent_messages_kept
        )

        # Add recent messages
        for msg in recent_messages:
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    async def maybe_summarize(self, chat_id: UUID, db: AsyncSession) -> None:
        """Check if messages should be summarized and perform if needed.

        Triggered after each message is added. Summarizes oldest batch when
        unsummarized message count exceeds threshold.

        Args:
            chat_id: ID of the chat
            db: Database session
        """
        # Set repository session
        self.chat_repo.db = db
        self.message_repo.db = db

        # Count unsummarized messages
        unsummarized_count = await self.message_repo.count_unsummarized(chat_id)

        # Check if summarization is needed
        if unsummarized_count <= self.settings.message_threshold:
            return

        # Get oldest messages to summarize
        all_unsummarized = await self.message_repo.get_unsummarized_by_chat(chat_id)

        # Take first N messages to summarize
        batch_to_summarize = all_unsummarized[: self.settings.summary_batch_size]

        if not batch_to_summarize:
            return

        # Format messages for summarization prompt
        formatted_messages = ""
        for msg in batch_to_summarize:
            role = "User" if msg.role == "user" else "Assistant"
            formatted_messages += f"{role}: {msg.content}\n"

        # Call LLM to summarize
        summary_prompt = (
            f"{self.settings.summarization_prompt}\n\n{formatted_messages}"
        )

        try:
            new_summary = await self.llm_service.completion(
                [
                    {
                        "role": "system",
                        "content": "You are a conversation summarizer. "
                        "Create a concise summary preserving key facts and context.",
                    },
                    {"role": "user", "content": summary_prompt},
                ],
                temperature=0.3,  # Lower temperature for more consistent summaries
            )
        except Exception as e:
            # Log error but don't fail - summarization is non-critical
            print(f"Summarization failed for chat {chat_id}: {str(e)}")
            return

        # Get chat and update summary
        chat = await self.chat_repo.get_by_id(chat_id)
        if not chat:
            return

        # Combine with existing summary if present
        if chat.summary:
            combined_summary = f"{chat.summary}\n\n[Later conversation]:\n{new_summary}"
        else:
            combined_summary = new_summary

        # Update chat with new summary (truncate if too long)
        max_summary_length = 2000
        if len(combined_summary) > max_summary_length:
            combined_summary = combined_summary[-max_summary_length:]

        await self.chat_repo.update(
            chat_id,
            summary=combined_summary,
        )

        # Mark messages as summarized
        message_ids = [msg.id for msg in batch_to_summarize]
        await self.message_repo.mark_as_summarized(message_ids)
