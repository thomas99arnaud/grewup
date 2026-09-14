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


@pytest.mark.asyncio
async def test_dossier_api_reads_and_writes_word(client: AsyncClient, tmp_path, monkeypatch):
    from docx import Document

    from backend.core.config import settings
    from backend.modules.applications.dossier import _compact_from_docx_cached

    path = tmp_path / "suivi-competences.docx"
    doc = Document()
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Compétence initiale"
    table.rows[0].cells[1].text = "Python"
    doc.save(path)
    monkeypatch.setattr(settings, "candidate_dossier_path", str(path))
    _compact_from_docx_cached.cache_clear()

    listed = await client.get("/api/profile/dossier")
    assert listed.status_code == 200
    body = listed.json()
    assert body["filename"] == "suivi-competences.docx"
    assert body["rows"][0][0]["text"] == "Compétence initiale"
    assert body["rows"][0][1]["text"] == "Python"

    updated = await client.put(
        "/api/profile/dossier",
        json={
            "rows": [
                ["IAS RAG", "Python, LangChain"],
                ["Ministère des Transports", "2025 | Montréal"],
            ]
        },
    )
    assert updated.status_code == 200
    rows = updated.json()["rows"]
    assert rows[0][0]["text"] == "IAS RAG"
    assert rows[1][1]["text"] == "2025 | Montréal"

    reloaded = (await client.get("/api/profile/dossier")).json()["rows"]
    assert reloaded[0][0]["text"] == "IAS RAG"
    from backend.modules.applications.dossier import load_rows

    assert load_rows()[0] == ["IAS RAG", "Python, LangChain"]
