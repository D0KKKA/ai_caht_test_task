"""Message service for message operations."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.repositories.message_repository import MessageRepository


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
