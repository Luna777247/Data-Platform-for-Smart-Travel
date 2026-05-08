import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@pytest.mark.asyncio
async def test_get_places():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/places")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)