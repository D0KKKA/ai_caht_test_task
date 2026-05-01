"""Chat API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import CHATS_PAGE_DEFAULT_LIMIT, PAGINATION_MAX_LIMIT
from app.core.database import get_db
from app.core.dependencies import (
    get_chat_repository,
    get_chat_service,
    get_client_id,
)
from app.core.rate_limit import WRITE_RATE_LIMIT, limiter
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatResponse])
async def list_chats(
    client_id: UUID = Depends(get_client_id),
    chat_repo: ChatRepository = Depends(get_chat_repository),
    limit: int = Query(default=CHATS_PAGE_DEFAULT_LIMIT, ge=1, le=PAGINATION_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """Список чатов клиента, отсортированный по updated_at DESC."""
    return await chat_repo.get_all_ordered(client_id, limit=limit, offset=offset)


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(WRITE_RATE_LIMIT)
async def create_chat(
    request: Request,
    response: Response,
    client_id: UUID = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
    chat_svc: ChatService = Depends(get_chat_service),
):
    """Создать новый пустой чат."""
    return await chat_svc.create_chat(client_id, db)


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: UUID,
    client_id: UUID = Depends(get_client_id),
    chat_repo: ChatRepository = Depends(get_chat_repository),
):
    """Получить чат по ID (проверяет принадлежность клиенту)."""
    chat = await chat_repo.get_by_id_and_client(chat_id, client_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(WRITE_RATE_LIMIT)
async def delete_chat(
    request: Request,
    response: Response,
    chat_id: UUID,
    client_id: UUID = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
    chat_svc: ChatService = Depends(get_chat_service),
):
    """Удалить чат по ID (каскадно удаляет сообщения)."""
    success = await chat_svc.delete_chat(chat_id, client_id, db)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
