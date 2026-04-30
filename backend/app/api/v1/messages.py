"""Message API endpoints with streaming."""

import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
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
from app.services.llm_service import get_llm_service
from app.services.context_service import ContextService
from app.services.chat_service import ChatService
from app.services.message_service import MessageService
from app.repositories.message_repository import MessageRepository
from app.repositories.chat_repository import ChatRepository
from app.schemas.message import MessageCreate, MessageResponse

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
    # Verify chat ownership
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
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Send a message and stream assistant response via SSE.

    Requires X-Client-Id header.

    Returns:
        StreamingResponse with SSE events
    """
    # Validate chat exists and belongs to client
    chat_repo = await get_chat_repository(db)
    chat = await chat_repo.get_by_id_and_client(chat_id, client_id)

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    # Validate message content
    if not payload.content or not payload.content.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Message content cannot be empty",
        )

    # Prepare services
    message_repo = await get_message_repository(db)
    message_svc = await get_message_service(message_repo)
    context_svc = await get_context_service(
        chat_repo,
        message_repo,
        get_llm_service(),
    )
    chat_svc = await get_chat_service(chat_repo, get_llm_service())
    llm_svc = get_llm_service()

    # Save user message
    user_message = await message_svc.create_user_message(
        chat_id, payload.content, db
    )

    async def generate_sse():
        """Generate SSE events for streaming response."""
        try:
            # Build context for LLM
            context = await context_svc.build_context(chat_id, db)

            # Stream from LLM
            accumulated_content = ""
            async for chunk in llm_svc.stream_completion(context):
                accumulated_content += chunk
                yield f"data: {json.dumps({'type': 'delta', 'content': chunk})}\n\n"

            # Save assistant message
            assistant_message = await message_svc.create_assistant_message(
                chat_id, accumulated_content, db
            )

            # Send done event
            yield f"data: {json.dumps({'type': 'done', 'message_id': str(assistant_message.id), 'content': accumulated_content})}\n\n"

            # Schedule background tasks
            # Need to create new DB context for background work
            async with get_db_context() as bg_db:
                # Update message count (user + assistant = 2)
                chat_repo_bg = await get_chat_repository(bg_db)
                await chat_repo_bg.update(chat_id, message_count=chat.message_count + 2)

                # Maybe generate title (if first message)
                if chat.message_count == 0:
                    chat_svc_bg = await get_chat_service(chat_repo_bg, get_llm_service())
                    await chat_svc_bg.maybe_generate_title(
                        chat_id, payload.content, bg_db
                    )

                # Maybe summarize (if needed)
                context_svc_bg = await get_context_service(
                    chat_repo_bg,
                    await get_message_repository(bg_db),
                    get_llm_service(),
                )
                await context_svc_bg.maybe_summarize(chat_id, bg_db)

        except Exception as e:
            # Send error event
            error_msg = str(e)
            yield f"data: {json.dumps({'type': 'error', 'detail': error_msg})}\n\n"

    return StreamingResponse(
        generate_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
