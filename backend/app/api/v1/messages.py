"""Message API endpoints with streaming."""

import asyncio
import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    MAX_ACCUMULATED_RESPONSE_CHARS,
    MESSAGES_PAGE_DEFAULT_LIMIT,
    PAGINATION_MAX_LIMIT,
)
from app.core.database import get_db, get_db_context
from app.core.dependencies import (
    get_message_repository,
    get_chat_repository,
    get_context_service,
    get_chat_service,
    get_message_service,
    get_client_id,
)
from app.core.rate_limit import WRITE_RATE_LIMIT, limiter
from app.services.llm_service import get_llm_service
from app.schemas.message import MessageCreate, MessageResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["messages"])


@router.get("/{chat_id}/messages", response_model=list[MessageResponse])
async def get_chat_messages(
    chat_id: UUID,
    client_id: UUID = Depends(get_client_id),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(
        default=MESSAGES_PAGE_DEFAULT_LIMIT,
        ge=1,
        le=PAGINATION_MAX_LIMIT,
    ),
    offset: int = Query(default=0, ge=0),
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
@limiter.limit(WRITE_RATE_LIMIT)
async def send_message(
    request: Request,
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

    content = payload.content.strip()
    message_repo = await get_message_repository(db)
    message_svc = await get_message_service(message_repo)
    context_svc = await get_context_service(
        chat_repo,
        message_repo,
        get_llm_service(),
    )
    llm_svc = get_llm_service()
    should_generate_title = False

    try:
        await message_svc.create_user_message(
            chat_id,
            content,
            db,
            commit=False,
        )
        updated_message_count = await chat_repo.increment_message_count(
            chat_id,
            1,
            commit=False,
        )
        if updated_message_count is None:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found",
            )

        await db.commit()
        should_generate_title = updated_message_count == 1 and chat.title is None
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        logger.error("Failed to persist user message for chat %s: %s", chat_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist message",
        )

    # Capture for closure
    first_message_content = content

    async def maybe_generate_title_task():
        """Generate the title asynchronously when the first user message arrives."""
        if not should_generate_title:
            return

        try:
            async with get_db_context() as bg_db:
                chat_repo_bg = await get_chat_repository(bg_db)
                chat_svc_bg = await get_chat_service(chat_repo_bg, get_llm_service())
                await chat_svc_bg.maybe_generate_title(
                    chat_id,
                    first_message_content,
                    bg_db,
                )
        except Exception as exc:
            logger.error("Title generation task failed for chat %s: %s", chat_id, exc)

    async def post_stream_tasks():
        """Run follow-up work that should not delay the done event."""
        await maybe_generate_title_task()

        try:
            async with get_db_context() as bg_db:
                chat_repo_bg = await get_chat_repository(bg_db)
                context_svc_bg = await get_context_service(
                    chat_repo_bg,
                    await get_message_repository(bg_db),
                    get_llm_service(),
                )
                await context_svc_bg.maybe_summarize(chat_id, bg_db)
        except Exception as exc:
            logger.error(
                "Post-stream summarization failed for chat %s: %s",
                chat_id,
                exc,
            )

    async def persist_assistant_message(content_to_store: str) -> str:
        """Persist the assistant message and atomically update the counter."""
        if not content_to_store:
            raise RuntimeError("LLM returned an empty response")

        async with get_db_context() as persist_db:
            chat_repo_bg = await get_chat_repository(persist_db)
            message_repo_bg = await get_message_repository(persist_db)
            message_svc_bg = await get_message_service(message_repo_bg)

            assistant_message = await message_svc_bg.create_assistant_message(
                chat_id,
                content_to_store,
                persist_db,
                commit=False,
            )
            updated_message_count = await chat_repo_bg.increment_message_count(
                chat_id,
                1,
                commit=False,
            )
            if updated_message_count is None:
                await persist_db.rollback()
                raise RuntimeError("Chat disappeared while persisting assistant message")

            await persist_db.commit()
            return str(assistant_message.id)

    async def generate_sse():
        """Generate SSE events for streaming response."""
        try:
            context = await context_svc.build_context(chat_id, db)

            # Stream from LLM — yield all chunks to client, but cap what we store
            accumulated_content = ""
            async for chunk in llm_svc.stream_completion(context):
                if await request.is_disconnected():
                    logger.info(
                        "Client disconnected while streaming response for chat %s",
                        chat_id,
                    )
                    asyncio.create_task(maybe_generate_title_task())
                    return

                yield f"data: {json.dumps({'type': 'delta', 'content': chunk})}\n\n"
                if len(accumulated_content) < MAX_ACCUMULATED_RESPONSE_CHARS:
                    remaining_chars = (
                        MAX_ACCUMULATED_RESPONSE_CHARS - len(accumulated_content)
                    )
                    accumulated_content += chunk[:remaining_chars]

            assistant_message_id = await persist_assistant_message(accumulated_content)
            asyncio.create_task(post_stream_tasks())
            yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message_id, 'content': accumulated_content})}\n\n"

        except HTTPException as e:
            logger.warning("HTTPException in SSE stream for chat %s: %s", chat_id, e.detail)
            asyncio.create_task(maybe_generate_title_task())
            yield f"data: {json.dumps({'type': 'error', 'detail': e.detail})}\n\n"
        except Exception as e:
            logger.error("Unexpected error in SSE stream for chat %s: %s", chat_id, e, exc_info=True)
            asyncio.create_task(maybe_generate_title_task())
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
