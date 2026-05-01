"""Message service for message operations."""

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository

logger = logging.getLogger(__name__)


class MessageService:
    """Service for message operations."""

    def __init__(self, message_repo: MessageRepository):
        """Initialize message service with dependencies."""
        self.message_repo = message_repo

    async def create_user_message(
        self,
        chat_id: UUID,
        content: str,
        db: AsyncSession,
        *,
        commit: bool = True,
    ) -> Message:
        """Create a user message in the chat.

        Args:
            chat_id: ID of the chat
            content: Message content
            db: Database session

        Returns:
            Created Message object
        """
        self.message_repo.db = db

        message = Message(chat_id=chat_id, role="user", content=content)
        return await self.message_repo.create(message, commit=commit)

    async def create_assistant_message(
        self,
        chat_id: UUID,
        content: str,
        db: AsyncSession,
        *,
        commit: bool = True,
    ) -> Message:
        """Create an assistant message in the chat.

        Args:
            chat_id: ID of the chat
            content: Message content
            db: Database session

        Returns:
            Created Message object
        """
        self.message_repo.db = db

        message = Message(chat_id=chat_id, role="assistant", content=content)
        return await self.message_repo.create(message, commit=commit)

    async def get_chat_messages(
        self, chat_id: UUID, db: AsyncSession, limit: int = 100, offset: int = 0
    ) -> list[Message]:
        """Get all messages for a chat ordered by created_at ASC.

        Args:
            chat_id: ID of the chat
            db: Database session
            limit: Number of messages to return
            offset: Number of messages to skip

        Returns:
            List of Message objects
        """
        self.message_repo.db = db
        return await self.message_repo.get_by_chat_id(
            chat_id, limit=limit, offset=offset
        )

    async def save_user_message(
        self,
        chat_id: UUID,
        content: str,
        db: AsyncSession,
        chat_repo: ChatRepository,
    ) -> tuple[int, bool]:
        """Atomically persist a user message and update the chat message count.

        Returns:
            (message_count, is_first_message) — the new total count and whether
            this was the first message in the chat.
        """
        try:
            await self.create_user_message(chat_id, content, db, commit=False)
            count = await chat_repo.increment_message_count(chat_id, 1, commit=False)
            if count is None:
                await db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found"
                )
            await db.commit()
            return count, count == 1
        except HTTPException:
            raise
        except Exception as exc:
            await db.rollback()
            logger.error("Failed to persist user message for chat %s: %s", chat_id, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to persist message",
            ) from exc

    async def update_message_content(
        self,
        message_id: UUID,
        content: str,
        db: AsyncSession,
        *,
        commit: bool = True,
    ) -> Message | None:
        """Replace stored content for an existing message."""
        self.message_repo.db = db
        return await self.message_repo.update(
            message_id,
            content=content,
            commit=commit,
        )
