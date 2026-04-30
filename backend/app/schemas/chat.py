"""Pydantic schemas for Chat request/response models."""

from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class ChatCreate(BaseModel):
    """Schema for creating a new chat (client_id comes from header)."""

    pass


class ChatResponse(BaseModel):
    """Schema for chat responses."""

    id: UUID = Field(description="Unique chat ID")
    client_id: UUID = Field(description="Anonymous user ID")
    title: str | None = Field(default=None, description="Chat title (null during generation)")
    created_at: datetime = Field(description="When the chat was created")
    updated_at: datetime = Field(description="When the chat was last updated")
    message_count: int = Field(default=0, description="Total number of messages")

    class Config:
        from_attributes = True
