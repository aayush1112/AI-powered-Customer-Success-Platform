from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Generic async repository for SQLAlchemy 2.0 models.

    Provides create / get_by_id / get_all / update / delete / count.
    All mutations call session.flush() so the caller's unit-of-work
    controls when the transaction is committed.
    """

    def __init__(self, model: type[ModelT], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def create(self, **kwargs: Any) -> ModelT:
        """Instantiate, persist, and refresh a new model instance."""
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, id: UUID) -> ModelT | None:
        """Fetch a single row by primary key; returns None if not found."""
        return await self.session.get(self.model, id)

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelT]:
        """Return a paginated list of all rows for this model."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, instance: ModelT, **kwargs: Any) -> ModelT:
        """Apply kwargs to an existing instance, flush, and refresh it."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        """Delete a model instance and flush the change."""
        await self.session.delete(instance)
        await self.session.flush()

    async def count(self) -> int:
        """Return the total row count for this model's table."""
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()
