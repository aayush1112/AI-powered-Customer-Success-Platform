"""Unit tests for CustomerService — repository is fully mocked."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.enums import CustomerStatus
from app.schemas.customer import CustomerCreate, CustomerListParams, CustomerUpdate
from app.services.customer_service import CustomerService


@pytest.fixture
def service() -> CustomerService:
    svc = CustomerService(MagicMock())
    svc._repo = MagicMock()
    svc._repo.get_active_by_id = AsyncMock()
    svc._repo.create = AsyncMock()
    svc._repo.update = AsyncMock()
    svc._repo.soft_delete = AsyncMock()
    svc._repo.get_paginated = AsyncMock()
    return svc


@pytest.fixture
def create_data() -> CustomerCreate:
    return CustomerCreate(
        company_name="Acme Corp",
        contact_name="Jane Doe",
        contact_email="jane@acme.com",
    )


# ── get_by_id ─────────────────────────────────────────────────────────────────


class TestGetById:
    async def test_returns_customer_when_found(self, service):
        customer = MagicMock()
        service._repo.get_active_by_id.return_value = customer
        result = await service.get_by_id(uuid.uuid4())
        assert result is customer

    async def test_raises_404_when_not_found(self, service):
        service._repo.get_active_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            await service.get_by_id(uuid.uuid4())
        assert exc.value.status_code == 404

    async def test_passes_correct_id_to_repo(self, service):
        cid = uuid.uuid4()
        customer = MagicMock()
        service._repo.get_active_by_id.return_value = customer
        await service.get_by_id(cid)
        service._repo.get_active_by_id.assert_called_once_with(cid)


# ── create ────────────────────────────────────────────────────────────────────


class TestCreate:
    async def test_delegates_all_fields_to_repo(self, service, create_data):
        customer = MagicMock()
        service._repo.create.return_value = customer
        created_by = uuid.uuid4()

        result = await service.create(create_data, created_by)

        assert result is customer
        service._repo.create.assert_called_once()
        kw = service._repo.create.call_args.kwargs
        assert kw["company_name"] == create_data.company_name
        assert kw["contact_name"] == create_data.contact_name
        assert kw["contact_email"] == str(create_data.contact_email)
        assert kw["created_by"] == created_by

    async def test_optional_fields_forwarded(self, service):
        customer = MagicMock()
        service._repo.create.return_value = customer

        data = CustomerCreate(
            company_name="Corp",
            industry="Fintech",
            contact_name="Bob",
            contact_email="bob@corp.com",
            contact_phone="+14155551234",
        )
        await service.create(data, uuid.uuid4())
        kw = service._repo.create.call_args.kwargs
        assert kw["industry"] == "Fintech"
        assert kw["contact_phone"] == "+14155551234"


# ── update ────────────────────────────────────────────────────────────────────


class TestUpdate:
    async def test_raises_404_when_customer_not_found(self, service):
        service._repo.get_active_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            await service.update(uuid.uuid4(), CustomerUpdate(status=CustomerStatus.ACTIVE))
        assert exc.value.status_code == 404

    async def test_empty_update_returns_unchanged_customer(self, service):
        customer = MagicMock()
        service._repo.get_active_by_id.return_value = customer

        result = await service.update(uuid.uuid4(), CustomerUpdate())

        service._repo.update.assert_not_called()
        assert result is customer

    async def test_single_field_update_calls_repo(self, service):
        customer = MagicMock()
        updated = MagicMock()
        service._repo.get_active_by_id.return_value = customer
        service._repo.update.return_value = updated

        result = await service.update(uuid.uuid4(), CustomerUpdate(status=CustomerStatus.ACTIVE))

        service._repo.update.assert_called_once_with(customer, status=CustomerStatus.ACTIVE)
        assert result is updated

    async def test_contact_email_converted_to_string(self, service):
        customer = MagicMock()
        service._repo.get_active_by_id.return_value = customer
        service._repo.update.return_value = MagicMock()

        await service.update(
            uuid.uuid4(),
            CustomerUpdate(contact_email="new@example.com"),  # type: ignore[arg-type]
        )
        kw = service._repo.update.call_args.kwargs
        assert isinstance(kw["contact_email"], str)


# ── delete ────────────────────────────────────────────────────────────────────


class TestDelete:
    async def test_raises_404_when_not_found(self, service):
        service._repo.get_active_by_id.return_value = None
        with pytest.raises(HTTPException) as exc:
            await service.delete(uuid.uuid4())
        assert exc.value.status_code == 404

    async def test_calls_soft_delete_with_customer(self, service):
        customer = MagicMock()
        service._repo.get_active_by_id.return_value = customer

        await service.delete(uuid.uuid4())

        service._repo.soft_delete.assert_called_once_with(customer)


# ── get_paginated ─────────────────────────────────────────────────────────────


class TestGetPaginated:
    async def test_empty_db_returns_valid_response(self, service):
        service._repo.get_paginated.return_value = ([], 0)

        params = CustomerListParams(page=1, page_size=10)
        result = await service.get_paginated(params)

        assert result.total == 0
        assert result.page == 1
        assert result.page_size == 10
        assert result.items == []
        assert result.pages == 1

    async def test_pagination_math(self, service):
        service._repo.get_paginated.return_value = ([], 25)
        params = CustomerListParams(page=1, page_size=10)
        result = await service.get_paginated(params)
        assert result.pages == 3  # ceil(25/10)

    async def test_passes_all_filter_params_to_repo(self, service):
        service._repo.get_paginated.return_value = ([], 0)
        params = CustomerListParams(
            page=2,
            page_size=5,
            search="acme",
            status=CustomerStatus.ACTIVE,
            industry="SaaS",
            sort_by="company_name",
            sort_order="asc",
        )
        await service.get_paginated(params)
        kw = service._repo.get_paginated.call_args.kwargs
        assert kw["page"] == 2
        assert kw["page_size"] == 5
        assert kw["search"] == "acme"
        assert kw["status"] == CustomerStatus.ACTIVE
        assert kw["industry"] == "SaaS"
        assert kw["sort_by"] == "company_name"
        assert kw["sort_order"] == "asc"
