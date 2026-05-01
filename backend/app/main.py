"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import init_db, close_db
from app.core.rate_limit import limiter
from app.api.v1.router import router as api_v1_router
from app.services.llm_service import close_llm_service

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
    await close_llm_service()
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
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
