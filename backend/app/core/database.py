"""Database setup with async SQLAlchemy and SQLite."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager

from app.core.config import get_settings

# Base class for all ORM models
Base = declarative_base()

# Cached engine and session factory (initialized at startup)
_engine: AsyncEngine | None = None
_async_session_maker: sessionmaker | None = None


async def init_db() -> None:
    """Initialize database engine and session factory."""
    global _engine, _async_session_maker

    settings = get_settings()

    # Create async engine with SQLite
    _engine = create_async_engine(
        settings.database_url,
        echo=False,  # Set to True for SQL debug logging
        future=True,
    )

    # Session factory
    _async_session_maker = sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create all tables
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connection."""
    global _engine

    if _engine:
        await _engine.dispose()
        _engine = None


async def get_db() -> AsyncSession:
    """FastAPI dependency to get a database session."""
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _async_session_maker() as session:
        yield session


@asynccontextmanager
async def get_db_context():
    """Context manager for getting a database session (for services/background tasks)."""
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _async_session_maker() as session:
        yield session
