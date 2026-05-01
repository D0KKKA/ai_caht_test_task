"""Message API endpoints with streaming."""

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, get_db_context
from app.core.dependencies import (
    get_message_repository,
    get_chat_repository,
    get_context_service,
    get_chat_service,
    get_message_service,
    get_client_id,
)
from app.core.constants import MAX_ACCUMULATED_RESPONSE_CHARS
from app.services.llm_service import get_llm_service
from app.repositories.message_repository import MessageRepository
from app.repositories.chat_repository import ChatRepository
from app.schemas.message import MessageCreate, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["messages"])


@router.get("/{chat_id}/messages", response_model=list[MessageResponse])
async def get_chat_messages(
    chat_id: UUID,
    client_id: UUID = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
):
    """Get all messages for a chat (validates ownership).

    Requires X-Client-Id header.
    """
    chat_repo = await get_chat_repository(db)
    chat = await chat_repo.get_by_id_and_client(chat_id, client_id)

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    message_repo = await get_message_repository(db)
    messages = await message_repo.get_by_chat_id(chat_id, limit=limit, offset=offset)

    return messages


@router.post("/{chat_id}/messages")
async def send_message(
    chat_id: UUID,
    payload: MessageCreate,
    client_id: UUID = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and stream assistant response via SSE.

    Requires X-Client-Id header.

    Returns:
        StreamingResponse with SSE events
    """
    chat_repo = await get_chat_repository(db)
    chat = await chat_repo.get_by_id_and_client(chat_id, client_id)

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    if not payload.content or not payload.content.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message content cannot be empty",
        )

    message_repo = await get_message_repository(db)
    message_svc = await get_message_service(message_repo)
    context_svc = await get_context_service(
        chat_repo,
        message_repo,
        get_llm_service(),
    )
    chat_svc = await get_chat_service(chat_repo, get_llm_service())
    llm_svc = get_llm_service()

    user_message = await message_svc.create_user_message(
        chat_id, payload.content, db
    )

    # Capture for closure
    first_message_content = payload.content
    prev_message_count = chat.message_count

    async def generate_sse():
        """Generate SSE events for streaming response."""
        try:
            context = await context_svc.build_context(chat_id, db)

            # Stream from LLM — yield all chunks to client, but cap what we store
            accumulated_content = ""
            async for chunk in llm_svc.stream_completion(context):
                yield f"data: {json.dumps({'type': 'delta', 'content': chunk})}\n\n"
                if len(accumulated_content) < MAX_ACCUMULATED_RESPONSE_CHARS:
                    accumulated_content += chunk

            # Save assistant message
            assistant_message = await message_svc.create_assistant_message(
                chat_id, accumulated_content, db
            )

            yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_message.id), 'content': accumulated_content})}\n\n"

            # Post-stream work in a fresh DB context
            try:
                async with get_db_context() as bg_db:
                    chat_repo_bg = await get_chat_repository(bg_db)
                    await chat_repo_bg.update(chat_id, message_count=prev_message_count + 2)

                    if prev_message_count == 0:
                        chat_svc_bg = await get_chat_service(chat_repo_bg, get_llm_service())
                        await chat_svc_bg.maybe_generate_title(
                            chat_id, first_message_content, bg_db
                        )

                    context_svc_bg = await get_context_service(
                        chat_repo_bg,
                        await get_message_repository(bg_db),
                        get_llm_service(),
                    )
                    await context_svc_bg.maybe_summarize(chat_id, bg_db)
            except Exception as bg_exc:
                logger.error(
                    "Post-stream background work failed for chat %s: %s",
                    chat_id,
                    bg_exc,
                )

        except HTTPException as e:
            logger.warning("HTTPException in SSE stream for chat %s: %s", chat_id, e.detail)
            yield f"data: {json.dumps({'type': 'error', 'detail': e.detail})}\n\n"
        except Exception as e:
            logger.error("Unexpected error in SSE stream for chat %s: %s", chat_id, e, exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'detail': 'Internal server error'})}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
