"""Dependency injection configuration."""

from functools import lru_cache
from uuid import UUID
from fastapi import Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.services.llm_service import LLMService, get_llm_service
from app.services.context_service import ContextService
from app.services.chat_service import ChatService
from app.services.message_service import MessageService


async def get_client_id(x_client_id: str = Header(..., alias="X-Client-Id")) -> UUID:
    """Extract and validate anonymous user ID from request header.

    Args:
        x_client_id: X-Client-Id header value (UUID string)

    Returns:
        UUID of the client

    Raises:
        ValueError: If not a valid UUID
    """
    try:
        return UUID(x_client_id)
    except ValueError:
        raise ValueError(f"Invalid X-Client-Id: {x_client_id}")


async def get_chat_repository(db: AsyncSession) -> ChatRepository:
    """Dependency: Chat repository."""
    return ChatRepository(db)


async def get_message_repository(db: AsyncSession) -> MessageRepository:
    """Dependency: Message repository."""
    return MessageRepository(db)


async def get_context_service(
    chat_repo: ChatRepository,
    message_repo: MessageRepository,
    llm: LLMService,
) -> ContextService:
    """Dependency: Context service."""
    return ContextService(chat_repo, message_repo, llm)


async def get_chat_service(
    chat_repo: ChatRepository,
    llm: LLMService,
) -> ChatService:
    """Dependency: Chat service."""
    return ChatService(chat_repo, llm)


async def get_message_service(
    message_repo: MessageRepository,
) -> MessageService:
    """Dependency: Message service."""
    return MessageService(message_repo)
