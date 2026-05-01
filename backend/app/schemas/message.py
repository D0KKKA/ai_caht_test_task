"""Pydantic schemas for Message request/response models."""

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field
from app.core.constants import MAX_MESSAGE_INPUT_CHARS


class MessageBase(BaseModel):
    """Base message schema with common fields."""

    role: str = Field(description="Message role: 'user' or 'assistant'")
    content: str = Field(min_length=1, description="Message content")


class MessageCreate(BaseModel):
    """Schema for creating a new message (user input)."""

    content: str = Field(min_length=1, max_length=MAX_MESSAGE_INPUT_CHARS, description="Message content")


class MessageResponse(MessageBase):
    """Schema for message responses."""

    id: UUID = Field(description="Unique message ID")
    chat_id: UUID = Field(description="ID of the chat this message belongs to")
    created_at: datetime = Field(description="When the message was created")
    is_summarized: bool = Field(default=False, description="Whether this message was summarized")

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Schema for listing messages."""

    messages: list[MessageResponse] = Field(description="List of messages")

    class Config:
        from_attributes = True


class SSEEvent(BaseModel):
    """Schema for Server-Sent Events."""

    type: str = Field(description="Event type: 'delta', 'done', or 'error'")
    content: str | None = Field(default=None, description="Content chunk or full message")
    message_id: UUID | None = Field(default=None, description="ID of the message (for done event)")
    detail: str | None = Field(default=None, description="Error detail (for error event)")
