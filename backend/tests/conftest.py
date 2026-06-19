from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.core.config import settings
from app.db.base import Base
import app.models  # noqa: F401 — registers all models with Base.metadata
from app.main import app

TEST_DATABASE_URL = settings.DATABASE_URL

_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=None)
_TestSession: async_sessionmaker[AsyncSession] = async_sessionmaker(
    _engine, class_=AsyncSession, expire_on_commit=False
)

# ── PostgreSQL enum DDL ───────────────────────────────────────────────────────
_ENUM_UP = [
    "CREATE TYPE IF NOT EXISTS userrole AS ENUM ('ADMIN', 'MANAGER', 'VIEWER')",
    "CREATE TYPE IF NOT EXISTS customerstatus AS ENUM ('ACTIVE', 'AT_RISK', 'CHURNED', 'PROSPECT')",
    "CREATE TYPE IF NOT EXISTS interactiontype AS ENUM ('MEETING', 'CALL', 'EMAIL', 'QBR')",
    "CREATE TYPE IF NOT EXISTS sentimenttype AS ENUM ('POSITIVE', 'NEUTRAL', 'NEGATIVE')",
]
_ENUM_DOWN = [
    "DROP TYPE IF EXISTS sentimenttype",
    "DROP TYPE IF EXISTS interactiontype",
    "DROP TYPE IF EXISTS customerstatus",
    "DROP TYPE IF EXISTS userrole",
]


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    async with _engine.begin() as conn:
        for stmt in _ENUM_UP:
            await conn.execute(text(stmt))
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        for stmt in _ENUM_DOWN:
            await conn.execute(text(stmt))
    await _engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    async with _TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
