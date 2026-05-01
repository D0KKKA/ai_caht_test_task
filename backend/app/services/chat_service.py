"""Chat service for chat operations and management."""

import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import Chat
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.services.llm_service import LLMService
from app.core.constants import TEMPERATURE_TITLE_GENERATION, TITLE_MAX_LENGTH
from app.core.prompts import TITLE_GENERATION_PROMPT

logger = logging.getLogger(__name__)


class ChatService:
    """Service for chat operations."""

    def __init__(
        self,
        chat_repo: ChatRepository,
        llm_service: LLMService,
    ):
        """Initialize chat service with dependencies."""
        self.chat_repo = chat_repo
        self.llm_service = llm_service

    async def create_chat(self, client_id: UUID, db: AsyncSession) -> Chat:
        """Create a new empty chat for a client.

        Args:
            client_id: ID of the anonymous user
            db: Database session

        Returns:
            Created Chat object with title=None (will be generated asynchronously)
        """
        self.chat_repo.db = db

        chat = Chat(client_id=client_id, title=None, message_count=0)
        return await self.chat_repo.create(chat)

    async def get_chat(self, chat_id: UUID, client_id: UUID, db: AsyncSession) -> Chat | None:
        """Get chat by ID (validates ownership).

        Args:
            chat_id: ID of the chat
            client_id: ID of the anonymous user
            db: Database session

        Returns:
            Chat object or None if not found or doesn't belong to client
        """
        self.chat_repo.db = db
        return await self.chat_repo.get_by_id_and_client(chat_id, client_id)

    async def get_all_chats(
        self, client_id: UUID, db: AsyncSession, limit: int = 50, offset: int = 0
    ) -> list[Chat]:
        """Get all chats for a client ordered by updated_at DESC.

        Args:
            client_id: ID of the anonymous user
            db: Database session
            limit: Number of chats to return
            offset: Number of chats to skip

        Returns:
            List of Chat objects belonging to the client
        """
        self.chat_repo.db = db
        return await self.chat_repo.get_all_ordered(
            client_id, limit=limit, offset=offset
        )

    async def delete_chat(self, chat_id: UUID, client_id: UUID, db: AsyncSession) -> bool:
        """Delete chat by ID (validates ownership, cascades to messages).

        Args:
            chat_id: ID of the chat
            client_id: ID of the anonymous user
            db: Database session

        Returns:
            True if deleted, False if not found or doesn't belong to client
        """
        self.chat_repo.db = db
        # Verify ownership first
        chat = await self.chat_repo.get_by_id_and_client(chat_id, client_id)
        if not chat:
            return False
        return await self.chat_repo.delete(chat_id)

    async def increment_message_count(
        self, chat_id: UUID, count: int, db: AsyncSession
    ) -> None:
        """Increment message count for a chat.

        Args:
            chat_id: ID of the chat
            count: Number to add to message_count
            db: Database session
        """
        self.chat_repo.db = db
        await self.chat_repo.increment_message_count(chat_id, count)

    async def maybe_generate_title(
        self, chat_id: UUID, first_message: str, db: AsyncSession
    ) -> None:
        """Generate title if chat has no title (called for first message).

        Args:
            chat_id: ID of the chat
            first_message: Content of the first user message
            db: Database session
        """
        self.chat_repo.db = db

        chat = await self.chat_repo.get_by_id(chat_id)
        if not chat or chat.title is not None:
            # Title already generated or chat not found
            return

        # Generate title using LLM
        try:
            title = await self.llm_service.completion(
                [
                    {"role": "system", "content": TITLE_GENERATION_PROMPT},
                    {"role": "user", "content": first_message},
                ],
                temperature=TEMPERATURE_TITLE_GENERATION,
            )

            # Clean up title: strip whitespace and quotes
            title = title.strip().strip('"\'')

            # Truncate to reasonable length
            title = title[:TITLE_MAX_LENGTH]

            # Update chat with generated title only if still untitled.
            await self.chat_repo.set_title_if_absent(chat_id, title)
        except Exception as e:
            logger.error("Title generation failed for chat %s: %s", chat_id, e)
