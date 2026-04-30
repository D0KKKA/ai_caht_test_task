"""Message ORM model."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, func, ForeignKey, Index, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Message(Base):
    """Message model for storing chat history."""

    __tablename__ = "messages"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Foreign key to chat
    chat_id = Column(
        UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Message role: "user" or "assistant"
    role = Column(String(20), nullable=False)

    # Message content
    content = Column(Text, nullable=False)

    # Creation timestamp
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Flag: True = folded into chat.summary, False = active in context
    is_summarized = Column(Boolean, default=False, nullable=False, index=True)

    # Relationship back to chat
    chat = relationship("Chat", back_populates="messages")

    # Composite indexes for query optimization
    __table_args__ = (
        Index("idx_messages_chat_id_created", "chat_id", "created_at"),
        Index("idx_messages_chat_is_summarized", "chat_id", "is_summarized"),
    )

    def __repr__(self) -> str:
        return (
            f"<Message(id={self.id}, chat_id={self.chat_id}, "
            f"role={self.role!r}, is_summarized={self.is_summarized})>"
        )
