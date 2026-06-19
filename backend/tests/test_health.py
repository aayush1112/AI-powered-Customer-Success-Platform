import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_shape(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    data = response.json()

    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert "services" in data
    assert isinstance(data["services"], dict)


@pytest.mark.asyncio
async def test_health_status_value(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    data = response.json()
    assert data["status"] in ("healthy", "degraded")


@pytest.mark.asyncio
async def test_health_services_keys(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    services = response.json()["services"]
    assert "database" in services
    assert "redis" in services
