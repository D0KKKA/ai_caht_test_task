"""Base repository with generic async CRUD operations."""

import logging
from typing import TypeVar, Generic, Type, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Generic async repository for CRUD operations."""

    def __init__(self, model: Type[ModelT], db: AsyncSession):
        """Initialize repository with model class and database session."""
        self.model = model
        self.db = db

    async def create(self, obj: ModelT) -> ModelT:
        """Create and return a new object."""
        try:
            self.db.add(obj)
            await self.db.commit()
            await self.db.refresh(obj)
            return obj
        except IntegrityError as e:
            await self.db.rollback()
            logger.error("IntegrityError on create %s: %s", self.model.__name__, e)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database constraint violation",
            )

    async def get_by_id(self, id) -> ModelT | None:
        """Get object by primary key."""
        return await self.db.get(self.model, id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelT]:
        """Get all objects with optional pagination."""
        query = select(self.model).limit(limit).offset(offset)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def update(self, id, **kwargs) -> ModelT | None:
        """Update object by id and return updated object."""
        obj = await self.get_by_id(id)
        if not obj:
            return None

        for key, value in kwargs.items():
            setattr(obj, key, value)

        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, id) -> bool:
        """Delete object by id and return success status."""
        obj = await self.get_by_id(id)
        if not obj:
            return False

        await self.db.delete(obj)
        await self.db.commit()
        return True

    async def count(self) -> int:
        """Count all objects using SQL COUNT (does not load rows into memory)."""
        query = select(func.count(self.model.id))
        result = await self.db.execute(query)
        return result.scalar() or 0
