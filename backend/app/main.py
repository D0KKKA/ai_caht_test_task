"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db, init_db, close_db
from app.api.v1.router import router as api_v1_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for app startup and shutdown."""
    await init_db()
    logger.info("Database initialized")
    yield
    await close_db()
    logger.info("Database connection closed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="AI Chat API",
        description="API for AI chat application with OpenRouter integration",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS — no wildcard, no credentials
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-Client-Id"],
    )

    # Include API routes
    app.include_router(api_v1_router)

    @app.get("/health")
    async def health_check(request: Request):
        """Health check that verifies database connectivity."""
        from app.core.database import get_db_context
        async with get_db_context() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "ok"}

    return app


app = create_app()
