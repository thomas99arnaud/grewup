import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from backend.db.session import async_session_factory
from backend.modules.profile.models import (
    CandidateProfile,
    Education,
    Experience,
    ProfileLanguage,
    Skill,
)


@pytest.fixture(autouse=True)
async def clean_profile_tables():
    async with async_session_factory() as session:
        await session.execute(delete(Skill))
        await session.execute(delete(ProfileLanguage))
        await session.execute(delete(Experience))
        await session.execute(delete(Education))
        await session.execute(delete(CandidateProfile))
        await session.commit()


@pytest.mark.asyncio
async def test_get_profile_creates_default(client: AsyncClient):
    response = await client.get("/api/profile")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["skills"] == []
    assert data["languages"] == []
    assert data["experiences"] == []
    assert data["educations"] == []


@pytest.mark.asyncio
async def test_profile_sections_crud(client: AsyncClient):
    await client.put(
        "/api/profile",
        json={
            "full_name": "Alice Martin",
            "headline": "Dev Python",
            "summary": "5 ans d'experience",
        },
    )

    assert (await client.post("/api/profile/skills", json={"name": "Python", "level": "advanced", "category": "Technique"})).status_code == 201
    assert (await client.post("/api/profile/languages", json={"name": "Anglais", "level": "fluent"})).status_code == 201
    assert (await client.post("/api/profile/experiences", json={"title": "Dev", "company": "Acme", "is_current": True})).status_code == 201
    assert (await client.post("/api/profile/educations", json={"degree": "Master", "institution": "UTC"})).status_code == 201

    profile = (await client.get("/api/profile")).json()
    assert profile["full_name"] == "Alice Martin"
    assert len(profile["skills"]) == 1
    assert len(profile["languages"]) == 1
    assert len(profile["experiences"]) == 1
    assert len(profile["educations"]) == 1

    skill_id = profile["skills"][0]["id"]
    assert (await client.delete(f"/api/profile/skills/{skill_id}")).status_code == 204
    assert len((await client.get("/api/profile")).json()["skills"]) == 0
