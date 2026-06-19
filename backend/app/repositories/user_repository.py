from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import UserRole
from app.models.user import User
from app.repositories.base import BaseRepository

_SORTABLE = {
    "first_name": User.first_name,
    "email": User.email,
    "role": User.role,
    "is_active": User.is_active,
    "created_at": User.created_at,
}


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email address (case-sensitive)."""
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Return True if an account with this email already exists."""
        stmt = select(User.id).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_active_users(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Return paginated active users ordered by creation date."""
        stmt = (
            select(User)
            .where(User.is_active.is_(True))
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_role(
        self,
        role: UserRole,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """Return all active users with the given role."""
        stmt = (
            select(User)
            .where(User.role == role, User.is_active.is_(True))
            .order_by(User.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_paginated(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        role: UserRole | None = None,
        is_active: bool | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[User], int]:
        """Return a page of users with optional search, role filter, active filter, and sort."""
        filters = []

        if search:
            term = f"%{search}%"
            filters.append(
                or_(
                    User.first_name.ilike(term),
                    User.last_name.ilike(term),
                    User.email.ilike(term),
                )
            )

        if role is not None:
            filters.append(User.role == role)

        if is_active is not None:
            filters.append(User.is_active.is_(is_active))

        count_stmt = select(func.count()).select_from(User)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total: int = (await self.session.execute(count_stmt)).scalar_one()

        sort_col = _SORTABLE.get(sort_by, User.created_at)
        order_expr = sort_col.desc() if sort_order == "desc" else sort_col.asc()

        data_stmt = select(User).order_by(order_expr).offset((page - 1) * page_size).limit(page_size)
        if filters:
            data_stmt = data_stmt.where(*filters)
        result = await self.session.execute(data_stmt)
        return list(result.scalars().all()), total

    async def count_active_admins(self) -> int:
        """Return the number of currently active ADMIN users."""
        stmt = select(func.count()).select_from(User).where(
            User.role == UserRole.ADMIN,
            User.is_active.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
