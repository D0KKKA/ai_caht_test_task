"""Chat repository with domain-specific queries."""

from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, func, update

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

    async def increment_message_count(
        self,
        id: UUID,
        delta: int,
        *,
        commit: bool = True,
    ) -> int | None:
        """Atomically increment message_count and return the updated value."""
        stmt = (
            update(Chat)
            .where(Chat.id == id)
            .values(
                message_count=Chat.message_count + delta,
                updated_at=func.now(),
            )
            .returning(Chat.message_count)
        )
        result = await self.db.execute(stmt)
        new_count = result.scalar_one_or_none()
        if new_count is None:
            return None

        await self.db.flush()
        if commit:
            await self.db.commit()
        return new_count

    async def set_title_if_absent(
        self,
        id: UUID,
        title: str,
        *,
        commit: bool = True,
    ) -> bool:
        """Set a title only if the chat is still untitled."""
        stmt = (
            update(Chat)
            .where(and_(Chat.id == id, Chat.title.is_(None)))
            .values(title=title, updated_at=func.now())
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        if commit:
            await self.db.commit()
        return bool(result.rowcount)

    async def touch(self, id: UUID, *, commit: bool = True) -> bool:
        """Update chat.updated_at without changing message_count."""
        stmt = update(Chat).where(Chat.id == id).values(updated_at=func.now())
        result = await self.db.execute(stmt)
        await self.db.flush()
        if commit:
            await self.db.commit()
        return bool(result.rowcount)
