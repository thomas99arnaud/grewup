from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from backend.modules.applications.llm import LlmError

LONG_RAG_OFFER = (
    "Ingénieur IA / chatbot RAG\n"
    "Entreprise Alpha\n"
    "Missions : concevoir un chatbot RAG sécurisé, LLM LangChain, "
    "déploiement GPU, documentation technique."
)

LONG_RAG_OFFER_B = (
    "Ingénieur LLM — chatbot RAG\n"
    "Entreprise Beta\n"
    "Missions : assistant RAG, large language model, LangChain, "
    "déploiement GPU auprès des métiers."
)

FULL_FAKE = {
    "job_title": "Ingénieur logiciel / IA",
    "company": "Alpha",
    "language": "fr",
    "fit_summary": "Le RAG IAS colle à l'offre.",
    "emphasized_experiences": ["IAS RAG"],
    "omitted_experiences": ["MTQ", "IAS outil de configuration industrielle"],
    "cv_markdown": "Thomas ARNAUD – Ingénieur logiciel / IA\n\nEXPERIENCES PROFESSIONNELLES\nIAS RAG",
    "cover_letter": "Madame, Monsieur,\n\nJe postule chez Alpha.",
}

LETTER_FAKE = {
    "job_title": "Ingénieur LLM",
    "company": "Beta",
    "language": "fr",
    "fit_summary": "CV RAG réutilisé, lettre adaptée à Beta.",
    "cover_letter": "Madame, Monsieur,\n\nLettre pour Beta.",
}


@pytest.mark.asyncio
async def test_generate_requires_offer_text(client: AsyncClient):
    response = await client.post("/api/applications/generate", json={"offer_text": "trop court"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_generate_without_api_key(client: AsyncClient):
    with patch(
        "backend.modules.applications.service.llm.chat_json",
        new=AsyncMock(side_effect=LlmError("Clé API manquante. Ajoute OPENAI_API_KEY dans le fichier .env")),
    ):
        response = await client.post("/api/applications/generate", json={"offer_text": LONG_RAG_OFFER})
    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_persists_application(client: AsyncClient):
    with patch(
        "backend.modules.applications.service.llm.chat_json",
        new=AsyncMock(return_value=FULL_FAKE),
    ):
        response = await client.post("/api/applications/generate", json={"offer_text": LONG_RAG_OFFER})
    assert response.status_code == 200
    data = response.json()
    assert data["application_id"]
    assert data["reused"] is False
    assert data["company"] == "Alpha"
    assert data["cv_pdf_base64"]
    assert data["omitted_experiences"]

    listed = await client.get("/api/applications")
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == data["application_id"]

    detail = await client.get(f"/api/applications/{data['application_id']}")
    assert detail.status_code == 200
    assert "Je postule chez Alpha" in detail.json()["cover_letter"]


@pytest.mark.asyncio
async def test_generate_reuses_cv_for_same_signature(client: AsyncClient):
    mock = AsyncMock(side_effect=[FULL_FAKE, LETTER_FAKE])
    with patch("backend.modules.applications.service.llm.chat_json", new=mock):
        first = await client.post("/api/applications/generate", json={"offer_text": LONG_RAG_OFFER})
        second = await client.post("/api/applications/generate", json={"offer_text": LONG_RAG_OFFER_B})
    assert first.status_code == 200
    assert second.status_code == 200
    data = second.json()
    assert data["reused"] is True
    assert data["reused_from_id"] == first.json()["application_id"]
    assert data["company"] == "Beta"
    assert "Lettre pour Beta" in data["cover_letter"]
    assert "IAS RAG" in data["cv_markdown"]
    assert data["job_title"] == "Ingénieur LLM"
    assert data["cv_markdown"].startswith("Thomas ARNAUD – Ingénieur LLM")
    assert mock.call_count == 2
    letter_user = mock.call_args_list[1].args[1]
    assert "Ne rédige PAS de CV" in letter_user


@pytest.mark.asyncio
async def test_generate_force_skips_reuse(client: AsyncClient):
    second_full = {**FULL_FAKE, "company": "Beta", "cover_letter": "CV régénéré pour Beta."}
    mock = AsyncMock(side_effect=[FULL_FAKE, second_full])
    with patch("backend.modules.applications.service.llm.chat_json", new=mock):
        await client.post("/api/applications/generate", json={"offer_text": LONG_RAG_OFFER})
        forced = await client.post(
            "/api/applications/generate",
            json={"offer_text": LONG_RAG_OFFER_B, "force": True},
        )
    assert forced.status_code == 200
    data = forced.json()
    assert data["reused"] is False
    assert "CV régénéré" in data["cover_letter"]
    second_user = mock.call_args_list[1].args[1]
    assert "Ne rédige PAS de CV" not in second_user


@pytest.mark.asyncio
async def test_patch_application_status(client: AsyncClient):
    with patch(
        "backend.modules.applications.service.llm.chat_json",
        new=AsyncMock(return_value=FULL_FAKE),
    ):
        created = await client.post("/api/applications/generate", json={"offer_text": LONG_RAG_OFFER})
    app_id = created.json()["application_id"]
    patched = await client.patch(
        f"/api/applications/{app_id}",
        json={"status": "applied", "notes": "Envoyé lundi"},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["status"] == "applied"
    assert body["notes"] == "Envoyé lundi"
    assert body["applied_at"]

