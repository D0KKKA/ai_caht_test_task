"""API v1 router aggregating all endpoints."""

from fastapi import APIRouter

from app.api.v1 import chats, messages

router = APIRouter(prefix="/api/v1")

# Include chat routes
router.include_router(chats.router)

# Include message routes
router.include_router(messages.router)
