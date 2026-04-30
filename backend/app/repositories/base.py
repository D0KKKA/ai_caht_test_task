"""Base repository with generic async CRUD operations."""

from typing import TypeVar, Generic, Type, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

ModelT = TypeVar("ModelT")


class BaseRepository(Generic[ModelT]):
    """Generic async repository for CRUD operations."""

    def __init__(self, model: Type[ModelT], db: AsyncSession):
        """Initialize repository with model class and database session."""
        self.model = model
        self.db = db

    async def create(self, obj: ModelT) -> ModelT:
        """Create and return a new object."""
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

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
        """Count all objects."""
        query = select(self.model)
        result = await self.db.execute(query)
        return len(result.scalars().all())
