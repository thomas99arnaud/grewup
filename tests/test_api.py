import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_manual_offer(client: AsyncClient):
    response = await client.post(
        "/api/offers/manual",
        json={
            "title": "Dev Python",
            "company": "Test Corp",
            "description_raw": "Great job",
            "location": "Paris",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Dev Python"
    assert data["source"] == "manual"


@pytest.mark.asyncio
async def test_list_offers(client: AsyncClient):
    await client.post(
        "/api/offers/manual",
        json={"title": "Job 1", "company": "Co", "description_raw": ""},
    )
    response = await client.get("/api/offers")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
