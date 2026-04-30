"""Message repository with domain-specific queries."""

from typing import List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func

from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """Repository for Message operations."""

    def __init__(self, db: AsyncSession):
        """Initialize with Message model."""
        super().__init__(Message, db)

    async def get_by_chat_id(
        self,
        chat_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Message]:
        """Get all messages for a chat ordered by created_at ASC."""
        query = (
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_unsummarized_by_chat(self, chat_id: UUID) -> List[Message]:
        """Get all non-summarized messages for a chat ordered by created_at."""
        query = (
            select(Message)
            .where(
                and_(
                    Message.chat_id == chat_id,
                    Message.is_summarized == False,  # noqa: E712
                )
            )
            .order_by(Message.created_at.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_recent_unsummarized(
        self, chat_id: UUID, limit: int = 20
    ) -> List[Message]:
        """Get the N most recent non-summarized messages for context building."""
        query = (
            select(Message)
            .where(
                and_(
                    Message.chat_id == chat_id,
                    Message.is_summarized == False,  # noqa: E712
                )
            )
            .order_by(Message.created_at.asc())
        )
        result = await self.db.execute(query)
        all_messages = result.scalars().all()
        # Return only the last `limit` messages
        return all_messages[-limit:] if len(all_messages) > limit else all_messages

    async def count_unsummarized(self, chat_id: UUID) -> int:
        """Count non-summarized messages for a chat."""
        query = select(func.count(Message.id)).where(
            and_(
                Message.chat_id == chat_id,
                Message.is_summarized == False,  # noqa: E712
            )
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def mark_as_summarized(self, message_ids: List[UUID]) -> int:
        """Mark messages as summarized by their IDs. Returns count of updated rows."""
        if not message_ids:
            return 0

        query = (
            select(Message)
            .where(Message.id.in_(message_ids))
        )
        result = await self.db.execute(query)
        messages = result.scalars().all()

        for msg in messages:
            msg.is_summarized = True

        await self.db.commit()
        return len(messages)
