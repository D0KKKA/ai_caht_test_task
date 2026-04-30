"""Chat API endpoints."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_chat_repository, get_chat_service, get_client_id
from app.services.llm_service import get_llm_service
from app.schemas.chat import ChatResponse, ChatCreate

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatResponse])
async def list_chats(
    client_id: UUID = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """Get all chats for the client ordered by updated_at DESC.

    Requires X-Client-Id header.
    """
    chat_repo = await get_chat_repository(db)
    chats = await chat_repo.get_all_ordered(client_id, limit=limit, offset=offset)
    return chats


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    client_id: UUID = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new empty chat for the client.

    Requires X-Client-Id header.
    """
    chat_repo = await get_chat_repository(db)
    chat_svc = await get_chat_service(chat_repo, get_llm_service())
    chat = await chat_svc.create_chat(client_id, db)
    return chat


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: UUID,
    client_id: UUID = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific chat by ID (validates ownership).

    Requires X-Client-Id header.
    """
    chat_repo = await get_chat_repository(db)
    chat = await chat_repo.get_by_id_and_client(chat_id, client_id)

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    return chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: UUID,
    client_id: UUID = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat by ID (validates ownership, cascades to messages).

    Requires X-Client-Id header.
    """
    chat_repo = await get_chat_repository(db)
    chat_svc = await get_chat_service(chat_repo, get_llm_service())
    success = await chat_svc.delete_chat(chat_id, client_id, db)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    return None
