"""Integration tests for CustomerRepository — exercises the real PostgreSQL DB."""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.enums import CustomerStatus, UserRole
from app.models.customer import Customer
from app.models.user import User
from app.repositories.customer_repository import CustomerRepository


pytestmark = pytest.mark.asyncio


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def owner(db_session: AsyncSession) -> User:
    """Persistent user that owns test customers in this module."""
    user = User(
        first_name="Repo",
        last_name="Owner",
        email=f"owner_{uuid.uuid4().hex[:8]}@repo.test",
        password_hash=hash_password("Password123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def repo(db_session: AsyncSession) -> CustomerRepository:
    return CustomerRepository(db_session)


@pytest_asyncio.fixture
async def one_customer(repo: CustomerRepository, owner: User) -> Customer:
    return await repo.create(
        company_name=f"FixtureCo_{uuid.uuid4().hex[:6]}",
        industry="SaaS",
        contact_name="Fixture Contact",
        contact_email=f"fixture_{uuid.uuid4().hex[:6]}@co.test",
        contact_phone=None,
        created_by=owner.id,
    )


# ── Create ────────────────────────────────────────────────────────────────────


class TestCreate:
    async def test_persists_customer_with_correct_fields(self, repo, owner):
        c = await repo.create(
            company_name="New Corp",
            industry="Fintech",
            contact_name="Alice",
            contact_email="alice@newcorp.test",
            contact_phone="+14155559999",
            created_by=owner.id,
        )
        assert c.id is not None
        assert c.company_name == "New Corp"
        assert c.industry == "Fintech"
        assert c.contact_email == "alice@newcorp.test"

    async def test_default_status_is_prospect(self, repo, owner):
        c = await repo.create(
            company_name="ProspectCo",
            industry=None,
            contact_name="Bob",
            contact_email="bob@prospect.test",
            contact_phone=None,
            created_by=owner.id,
        )
        assert c.status == CustomerStatus.PROSPECT

    async def test_is_not_deleted_by_default(self, repo, owner):
        c = await repo.create(
            company_name="ActiveDefault",
            industry=None,
            contact_name="Carol",
            contact_email="carol@active.test",
            contact_phone=None,
            created_by=owner.id,
        )
        assert c.is_deleted is False

    async def test_optional_phone_can_be_none(self, repo, owner):
        c = await repo.create(
            company_name="NoPhone Corp",
            industry=None,
            contact_name="Dan",
            contact_email="dan@nophone.test",
            contact_phone=None,
            created_by=owner.id,
        )
        assert c.contact_phone is None


# ── get_active_by_id ──────────────────────────────────────────────────────────


class TestGetActiveById:
    async def test_returns_existing_customer(self, repo, one_customer):
        result = await repo.get_active_by_id(one_customer.id)
        assert result is not None
        assert result.id == one_customer.id

    async def test_returns_none_for_unknown_id(self, repo):
        result = await repo.get_active_by_id(uuid.uuid4())
        assert result is None

    async def test_returns_none_for_soft_deleted(self, repo, one_customer):
        await repo.soft_delete(one_customer)
        result = await repo.get_active_by_id(one_customer.id)
        assert result is None


# ── soft_delete ───────────────────────────────────────────────────────────────


class TestSoftDelete:
    async def test_sets_is_deleted_flag(self, repo, one_customer, db_session):
        await repo.soft_delete(one_customer)
        assert one_customer.is_deleted is True

    async def test_sets_deleted_at_timestamp(self, repo, one_customer):
        await repo.soft_delete(one_customer)
        assert one_customer.deleted_at is not None

    async def test_deleted_customer_not_found_by_get_active(self, repo, one_customer):
        await repo.soft_delete(one_customer)
        result = await repo.get_active_by_id(one_customer.id)
        assert result is None


# ── get_paginated ─────────────────────────────────────────────────────────────


class TestGetPaginated:
    async def test_includes_created_customer(self, repo, one_customer):
        items, total = await repo.get_paginated(page=1, page_size=200)
        ids = [c.id for c in items]
        assert one_customer.id in ids
        assert total >= 1

    async def test_excludes_soft_deleted(self, repo, owner):
        uid = uuid.uuid4().hex[:6]
        to_delete = await repo.create(
            company_name=f"ToDelete_{uid}",
            industry=None,
            contact_name="Temp",
            contact_email=f"temp_{uid}@del.test",
            contact_phone=None,
            created_by=owner.id,
        )
        await repo.soft_delete(to_delete)
        items, _ = await repo.get_paginated(page=1, page_size=200)
        assert all(c.id != to_delete.id for c in items)

    async def test_search_matches_company_name(self, repo, owner):
        uid = uuid.uuid4().hex[:6]
        name = f"SearchableFoo_{uid}"
        await repo.create(
            company_name=name,
            industry=None,
            contact_name="Searcher",
            contact_email=f"s_{uid}@search.test",
            contact_phone=None,
            created_by=owner.id,
        )
        items, total = await repo.get_paginated(page=1, page_size=100, search=name)
        assert total >= 1
        assert any(c.company_name == name for c in items)

    async def test_status_filter_restricts_results(self, repo, owner):
        uid = uuid.uuid4().hex[:6]
        # Create an ACTIVE customer
        active = await repo.create(
            company_name=f"ActiveFilter_{uid}",
            industry=None,
            contact_name="Filter",
            contact_email=f"filter_{uid}@active.test",
            contact_phone=None,
            created_by=owner.id,
        )
        await repo.update(active, status=CustomerStatus.ACTIVE)

        items, _ = await repo.get_paginated(
            page=1, page_size=200, status=CustomerStatus.ACTIVE
        )
        assert all(c.status == CustomerStatus.ACTIVE for c in items)

    async def test_page_size_limits_item_count(self, repo, owner):
        # Ensure there are enough rows
        for i in range(4):
            uid = uuid.uuid4().hex[:6]
            await repo.create(
                company_name=f"PageSize_{i}_{uid}",
                industry=None,
                contact_name="Pager",
                contact_email=f"pager_{i}_{uid}@test.test",
                contact_phone=None,
                created_by=owner.id,
            )
        items, total = await repo.get_paginated(page=1, page_size=2)
        assert len(items) <= 2
        assert total >= 4


# ── update ────────────────────────────────────────────────────────────────────


class TestUpdate:
    async def test_updates_single_field(self, repo, one_customer):
        await repo.update(one_customer, status=CustomerStatus.ACTIVE)
        assert one_customer.status == CustomerStatus.ACTIVE

    async def test_updates_multiple_fields(self, repo, one_customer):
        await repo.update(
            one_customer,
            company_name="Renamed Corp",
            industry="Healthcare",
        )
        assert one_customer.company_name == "Renamed Corp"
        assert one_customer.industry == "Healthcare"
