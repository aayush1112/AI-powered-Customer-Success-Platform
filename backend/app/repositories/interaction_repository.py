from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import InteractionType
from app.models.interaction import Interaction
from app.repositories.base import BaseRepository

_SORTABLE = {
    "meeting_date": Interaction.meeting_date,
    "created_at": Interaction.created_at,
    "title": Interaction.title,
}


class InteractionRepository(BaseRepository[Interaction]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Interaction, session)

    def _eager_options(self) -> list:
        return [
            selectinload(Interaction.customer),
            selectinload(Interaction.created_by_user),
        ]

    async def get_with_relations(self, interaction_id: UUID) -> Interaction | None:
        stmt = (
            select(Interaction)
            .where(Interaction.id == interaction_id)
            .options(*self._eager_options())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_paginated(
        self,
        *,
        page: int,
        page_size: int,
        search: str | None,
        customer_id: UUID | None,
        interaction_type: InteractionType | None,
        start_date: datetime | None,
        end_date: datetime | None,
        created_by: UUID | None,
        sort_by: str,
        sort_order: str,
    ) -> tuple[list[Interaction], int]:
        filters: list = []
        if search:
            term = f"%{search}%"
            filters.append(
                or_(
                    Interaction.title.ilike(term),
                    Interaction.notes.ilike(term),
                )
            )
        if customer_id is not None:
            filters.append(Interaction.customer_id == customer_id)
        if interaction_type is not None:
            filters.append(Interaction.interaction_type == interaction_type)
        if start_date is not None:
            filters.append(Interaction.meeting_date >= start_date)
        if end_date is not None:
            filters.append(Interaction.meeting_date <= end_date)
        if created_by is not None:
            filters.append(Interaction.created_by == created_by)

        count_stmt = select(func.count()).select_from(Interaction)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = (await self.session.execute(count_stmt)).scalar_one()

        sort_col = _SORTABLE.get(sort_by, Interaction.meeting_date)
        order_expr = sort_col.desc() if sort_order == "desc" else sort_col.asc()

        data_stmt = (
            select(Interaction)
            .options(*self._eager_options())
            .order_by(order_expr)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        if filters:
            data_stmt = data_stmt.where(*filters)
        result = await self.session.execute(data_stmt)
        return list(result.scalars().all()), total

    async def get_by_customer_id(
        self,
        customer_id: UUID,
        *,
        skip: int = 0,
        limit: int = 200,
    ) -> list[Interaction]:
        stmt = (
            select(Interaction)
            .where(Interaction.customer_id == customer_id)
            .options(*self._eager_options())
            .order_by(Interaction.meeting_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_date_range(
        self,
        start: datetime,
        end: datetime,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Interaction]:
        stmt = (
            select(Interaction)
            .where(
                Interaction.meeting_date >= start,
                Interaction.meeting_date <= end,
            )
            .options(*self._eager_options())
            .order_by(Interaction.meeting_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_type(
        self,
        interaction_type: InteractionType,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Interaction]:
        stmt = (
            select(Interaction)
            .where(Interaction.interaction_type == interaction_type)
            .options(*self._eager_options())
            .order_by(Interaction.meeting_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_created_by(
        self,
        user_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Interaction]:
        stmt = (
            select(Interaction)
            .where(Interaction.created_by == user_id)
            .options(*self._eager_options())
            .order_by(Interaction.meeting_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_for_customer(
        self,
        customer_id: UUID,
    ) -> Interaction | None:
        stmt = (
            select(Interaction)
            .where(Interaction.customer_id == customer_id)
            .options(*self._eager_options())
            .order_by(Interaction.meeting_date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
