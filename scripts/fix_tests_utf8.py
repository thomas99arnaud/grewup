from pathlib import Path

CONFTEST = '''import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Tests must never write into the dev database used by uvicorn / the UI.
TEST_DB = ROOT / "data" / "grew_test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{TEST_DB}"

import pytest
from httpx import ASGITransport, AsyncClient

from backend.db.base import Base
from backend.db.session import engine
from backend.main import app


@pytest.fixture(autouse=True)
async def isolated_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
'''

TEST_API = '''import pytest
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
'''

PROFILE_API = Path("tests/test_profile_api.py").read_text(encoding="utf-8")

for rel, content in [
    ("tests/conftest.py", CONFTEST),
    ("tests/test_api.py", TEST_API),
    ("tests/test_profile_api.py", PROFILE_API),
]:
    Path(rel).write_text(content, encoding="utf-8", newline="\n")
    print("wrote", rel)

import sqlite3
c = sqlite3.connect("data/grew.db")
n = c.execute("DELETE FROM offers WHERE source = 'MANUAL' AND title IN ('Dev Python', 'Job 1')").rowcount
c.commit()
print("deleted", n, "test offers from grew.db")
