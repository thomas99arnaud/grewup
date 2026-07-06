import os
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
