"""Message API endpoints with streaming."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.streaming import build_sse_response, stream_assistant_response
from app.core.constants import MESSAGES_PAGE_DEFAULT_LIMIT, PAGINATION_MAX_LIMIT
from app.core.database import get_db
from app.core.dependencies import (
    get_chat_repository,
    get_client_id,
    get_context_service,
    get_message_repository,
    get_message_service,
)
from app.core.rate_limit import WRITE_RATE_LIMIT, limiter
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.message import MessageCreate, MessageRegenerateRequest, MessageResponse
from app.services.context_service import ContextService
from app.services.llm_service import LLMService, get_llm_service
from app.services.message_service import MessageService
from app.services.stream_tasks import (
    persist_assistant_response,
    persist_regenerated_response,
    run_post_stream_tasks,
)

router = APIRouter(prefix="/chats", tags=["messages"])


@router.get("/{chat_id}/messages", response_model=list[MessageResponse])
async def get_chat_messages(
    chat_id: UUID,
    client_id: UUID = Depends(get_client_id),
    chat_repo: ChatRepository = Depends(get_chat_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    limit: int = Query(default=MESSAGES_PAGE_DEFAULT_LIMIT, ge=1, le=PAGINATION_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
):
    """Список сообщений чата (проверяет принадлежность клиенту)."""
    chat = await chat_repo.get_by_id_and_client(chat_id, client_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    return await message_repo.get_by_chat_id(chat_id, limit=limit, offset=offset)


@router.post("/{chat_id}/messages")
@limiter.limit(WRITE_RATE_LIMIT)
async def send_message(
    request: Request,
    chat_id: UUID,
    payload: MessageCreate,
    client_id: UUID = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
    chat_repo: ChatRepository = Depends(get_chat_repository),
    message_svc: MessageService = Depends(get_message_service),
    context_svc: ContextService = Depends(get_context_service),
    llm_svc: LLMService = Depends(get_llm_service),
):
    """Отправить сообщение и получить ответ ассистента через SSE."""
    chat = await chat_repo.get_by_id_and_client(chat_id, client_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    content = payload.content.strip()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message content cannot be empty",
        )

    message_count, is_first_message = await message_svc.save_user_message(
        chat_id, content, db, chat_repo
    )
    should_generate_title = is_first_message and chat.title is None

    return build_sse_response(
        stream_assistant_response(
            request=request,
            chat_id=chat_id,
            llm_svc=llm_svc,
            build_context=lambda: context_svc.build_context(chat_id, db),
            persist_response=lambda c: persist_assistant_response(chat_id, c),
            on_disconnect=lambda: run_post_stream_tasks(chat_id, content, False),
            on_error=lambda: run_post_stream_tasks(chat_id, content, False),
            on_success=lambda: run_post_stream_tasks(chat_id, content, should_generate_title),
        )
    )


@router.post("/{chat_id}/messages/regenerate")
@limiter.limit(WRITE_RATE_LIMIT)
async def regenerate_message(
    request: Request,
    chat_id: UUID,
    payload: MessageRegenerateRequest,
    client_id: UUID = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
    chat_repo: ChatRepository = Depends(get_chat_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
    context_svc: ContextService = Depends(get_context_service),
    llm_svc: LLMService = Depends(get_llm_service),
):
    """Перегенерировать последний ответ ассистента."""
    chat = await chat_repo.get_by_id_and_client(chat_id, client_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")

    last_message = await message_repo.get_latest_by_chat_id(chat_id)
    if not last_message or last_message.role != "assistant":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No assistant response available to regenerate",
        )

    return build_sse_response(
        stream_assistant_response(
            request=request,
            chat_id=chat_id,
            llm_svc=llm_svc,
            build_context=lambda: context_svc.build_context(
                chat_id, db, exclude_message_id=last_message.id
            ),
            persist_response=lambda c: persist_regenerated_response(
                last_message.id, chat_id, c
            ),
        )
    )
