from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import CustomerStatus
from app.models.customer import Customer
from app.repositories.base import BaseRepository

_SORTABLE = {
    "company_name": Customer.company_name,
    "created_at": Customer.created_at,
    "status": Customer.status,
    "updated_at": Customer.updated_at,
}


class CustomerRepository(BaseRepository[Customer]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Customer, session)

    # ── Soft-delete aware lookups ─────────────────────────────────────────────

    async def get_active_by_id(self, customer_id: UUID) -> Customer | None:
        """Fetch a non-deleted customer by PK."""
        stmt = select(Customer).where(
            Customer.id == customer_id,
            Customer.is_deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def soft_delete(self, instance: Customer) -> None:
        """Mark a customer as deleted without removing the row."""
        instance.is_deleted = True
        instance.deleted_at = datetime.now(UTC)
        await self.session.flush()

    # ── Paginated list with search / filter / sort ────────────────────────────

    async def get_paginated(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        status: CustomerStatus | None = None,
        industry: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Customer], int]:
        """Return a page of non-deleted customers plus the total matching count."""
        filters = [Customer.is_deleted.is_(False)]

        if search:
            term = f"%{search}%"
            filters.append(
                or_(
                    Customer.company_name.ilike(term),
                    Customer.contact_name.ilike(term),
                    Customer.contact_email.ilike(term),
                )
            )

        if status is not None:
            filters.append(Customer.status == status)

        if industry is not None:
            filters.append(Customer.industry.ilike(f"%{industry}%"))

        count_stmt = select(func.count()).select_from(Customer).where(*filters)
        total: int = (await self.session.execute(count_stmt)).scalar_one()

        sort_col = _SORTABLE.get(sort_by, Customer.created_at)
        order_expr = sort_col.desc() if sort_order == "desc" else sort_col.asc()

        data_stmt = (
            select(Customer)
            .where(*filters)
            .order_by(order_expr)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.session.execute(data_stmt)
        return list(result.scalars().all()), total

    # ── Legacy convenience methods (soft-delete aware) ────────────────────────

    async def get_by_status(
        self,
        status: CustomerStatus,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Customer]:
        stmt = (
            select(Customer)
            .where(Customer.status == status, Customer.is_deleted.is_(False))
            .order_by(Customer.company_name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_company_name(self, company_name: str) -> Customer | None:
        stmt = select(Customer).where(
            Customer.company_name == company_name,
            Customer.is_deleted.is_(False),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_by_company(
        self,
        query: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Customer]:
        stmt = (
            select(Customer)
            .where(
                Customer.company_name.ilike(f"%{query}%"),
                Customer.is_deleted.is_(False),
            )
            .order_by(Customer.company_name)
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
    ) -> list[Customer]:
        stmt = (
            select(Customer)
            .where(
                Customer.created_by == user_id,
                Customer.is_deleted.is_(False),
            )
            .order_by(Customer.company_name)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_status(self, status: CustomerStatus) -> int:
        stmt = (
            select(func.count())
            .select_from(Customer)
            .where(Customer.status == status, Customer.is_deleted.is_(False))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
