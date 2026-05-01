"""Dependency injection configuration."""

from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.services.chat_service import ChatService
from app.services.context_service import ContextService
from app.services.llm_service import LLMService, get_llm_service
from app.services.message_service import MessageService


async def get_client_id(x_client_id: str = Header(..., alias="X-Client-Id")) -> UUID:
    """Извлекает и валидирует анонимный ID пользователя из заголовка."""
    try:
        return UUID(x_client_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Client-Id: must be a valid UUID",
        )


async def get_chat_repository(
    db: AsyncSession = Depends(get_db),
) -> ChatRepository:
    return ChatRepository(db)


async def get_message_repository(
    db: AsyncSession = Depends(get_db),
) -> MessageRepository:
    return MessageRepository(db)


async def get_message_service(
    message_repo: MessageRepository = Depends(get_message_repository),
) -> MessageService:
    return MessageService(message_repo)


async def get_chat_service(
    chat_repo: ChatRepository = Depends(get_chat_repository),
    llm: LLMService = Depends(get_llm_service),
) -> ChatService:
    return ChatService(chat_repo, llm)


async def get_context_service(
    chat_repo: ChatRepository = Depends(get_chat_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    llm: LLMService = Depends(get_llm_service),
) -> ContextService:
    return ContextService(chat_repo, message_repo, llm)
