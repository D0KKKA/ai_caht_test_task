"""Background tasks that run after streaming completes."""

import logging
from uuid import UUID

from app.core.database import get_db_context
from app.repositories.chat_repository import ChatRepository
from app.repositories.message_repository import MessageRepository
from app.services.chat_service import ChatService
from app.services.context_service import ContextService
from app.services.llm_service import get_llm_service
from app.services.message_service import MessageService

logger = logging.getLogger(__name__)


async def persist_assistant_response(chat_id: UUID, content: str) -> str:
    """Persist the completed assistant message and update the chat message count."""
    if not content:
        raise RuntimeError("LLM returned an empty response")

    async with get_db_context() as db:
        message_repo = MessageRepository(db)
        chat_repo = ChatRepository(db)
        message_svc = MessageService(message_repo)

        message = await message_svc.create_assistant_message(
            chat_id, content, db, commit=False
        )
        count = await chat_repo.increment_message_count(chat_id, 1, commit=False)
        if count is None:
            await db.rollback()
            raise RuntimeError("Chat disappeared while persisting assistant message")

        await db.commit()
        return str(message.id)


async def persist_regenerated_response(
    message_id: UUID, chat_id: UUID, content: str
) -> str:
    """Update an existing assistant message with regenerated content."""
    if not content:
        raise RuntimeError("LLM returned an empty response")

    async with get_db_context() as db:
        message_repo = MessageRepository(db)
        chat_repo = ChatRepository(db)
        message_svc = MessageService(message_repo)

        message = await message_svc.update_message_content(
            message_id, content, db, commit=False
        )
        if message is None:
            await db.rollback()
            raise RuntimeError("Assistant message disappeared during regeneration")

        if not await chat_repo.touch(chat_id, commit=False):
            await db.rollback()
            raise RuntimeError("Chat disappeared while finalizing regeneration")

        await db.commit()
        return str(message.id)


async def run_post_stream_tasks(
    chat_id: UUID,
    first_message_content: str,
    should_generate_title: bool,
) -> None:
    """Run title generation and context summarization after streaming finishes."""
    if should_generate_title:
        try:
            async with get_db_context() as db:
                chat_repo = ChatRepository(db)
                await ChatService(chat_repo, get_llm_service()).maybe_generate_title(
                    chat_id, first_message_content, db
                )
        except Exception as exc:
            logger.error("Title generation failed for chat %s: %s", chat_id, exc)

    try:
        async with get_db_context() as db:
            chat_repo = ChatRepository(db)
            message_repo = MessageRepository(db)
            await ContextService(
                chat_repo, message_repo, get_llm_service()
            ).maybe_summarize(chat_id, db)
    except Exception as exc:
        logger.error("Post-stream summarization failed for chat %s: %s", chat_id, exc)
