"""SSE streaming utilities for assistant responses."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from uuid import UUID

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.core.constants import MAX_ACCUMULATED_RESPONSE_CHARS
from app.services.llm_service import LLMService, LLMServiceError

logger = logging.getLogger(__name__)


def schedule_background(callback: Callable[[], Awaitable[None]] | None) -> None:
    """Schedule a background coroutine as an asyncio task."""
    if callback is not None:
        asyncio.create_task(callback())


def build_sse_response(event_generator: AsyncGenerator[str, None]) -> StreamingResponse:
    """Wrap an async generator in a standard SSE StreamingResponse."""
    return StreamingResponse(
        event_generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


async def stream_assistant_response(
    *,
    request,
    chat_id: UUID,
    llm_svc: LLMService,
    build_context: Callable[[], Awaitable[list[dict]]],
    persist_response: Callable[[str], Awaitable[str]],
    on_disconnect: Callable[[], Awaitable[None]] | None = None,
    on_error: Callable[[], Awaitable[None]] | None = None,
    on_success: Callable[[], Awaitable[None]] | None = None,
) -> AsyncGenerator[str, None]:
    """Stream assistant tokens to the client and persist the completed response."""
    try:
        context = await build_context()

        accumulated_content = ""
        async for chunk in llm_svc.stream_completion(context):
            if await request.is_disconnected():
                logger.info(
                    "Client disconnected while streaming response for chat %s", chat_id
                )
                schedule_background(on_disconnect)
                return

            yield f"data: {json.dumps({'type': 'delta', 'content': chunk})}\n\n"
            if len(accumulated_content) < MAX_ACCUMULATED_RESPONSE_CHARS:
                remaining = MAX_ACCUMULATED_RESPONSE_CHARS - len(accumulated_content)
                accumulated_content += chunk[:remaining]

        message_id = await persist_response(accumulated_content)
        schedule_background(on_success)
        yield f"data: {json.dumps({'type': 'done', 'message_id': message_id, 'content': accumulated_content})}\n\n"

    except HTTPException as exc:
        logger.warning("HTTPException in SSE stream for chat %s: %s", chat_id, exc.detail)
        schedule_background(on_error)
        yield f"data: {json.dumps({'type': 'error', 'detail': exc.detail})}\n\n"
    except LLMServiceError as exc:
        logger.warning("LLM error in SSE stream for chat %s: %s", chat_id, exc)
        schedule_background(on_error)
        yield f"data: {json.dumps({'type': 'error', 'detail': str(exc)})}\n\n"
    except Exception as exc:
        logger.error(
            "Unexpected error in SSE stream for chat %s: %s", chat_id, exc, exc_info=True
        )
        schedule_background(on_error)
        yield f"data: {json.dumps({'type': 'error', 'detail': 'Internal server error'})}\n\n"
