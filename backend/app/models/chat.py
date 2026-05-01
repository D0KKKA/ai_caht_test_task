"""Chat ORM model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, func, UUID, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class Chat(Base):
    """Chat model for storing conversation metadata."""

    __tablename__ = "chats"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Anonymous user identifier
    client_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Chat title (NULL = "..." loading state during generation)
    title = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Summarized context from old messages (accumulated)
    summary = Column(Text, nullable=True)

    # Denormalized message count for sorting/display
    message_count = Column(Integer, default=0, nullable=False)

    # Relationship to messages
    messages = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Composite index for finding chats by client_id and ordering by updated_at
    __table_args__ = (
        Index("idx_chat_client_id_updated", "client_id", "updated_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Chat(id={self.id}, client_id={self.client_id}, title={self.title!r}, "
            f"message_count={self.message_count})>"
        )
