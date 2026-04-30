"""Chat repository with domain-specific queries."""

from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_

from app.models.chat import Chat
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[Chat]):
    """Repository for Chat operations."""

    def __init__(self, db: AsyncSession):
        """Initialize with Chat model."""
        super().__init__(Chat, db)

    async def get_all_ordered(
        self, client_id: UUID, limit: int = 50, offset: int = 0
    ) -> List[Chat]:
        """Get all chats for a client ordered by updated_at DESC."""
        query = (
            select(self.model)
            .where(self.model.client_id == client_id)
            .order_by(self.model.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_id_with_messages(self, id: UUID, client_id: UUID) -> Chat | None:
        """Get chat by id with all messages loaded (validates ownership)."""
        query = (
            select(Chat)
            .where(
                and_(
                    Chat.id == id,
                    Chat.client_id == client_id,
                )
            )
            .options(selectinload(Chat.messages))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_and_client(self, id: UUID, client_id: UUID) -> Chat | None:
        """Get chat by id, validating it belongs to the client."""
        query = select(Chat).where(
            and_(Chat.id == id, Chat.client_id == client_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
