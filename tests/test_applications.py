from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from backend.modules.applications.llm import LlmError


@pytest.mark.asyncio
async def test_generate_requires_offer_text(client: AsyncClient):
    response = await client.post("/api/applications/generate", json={"offer_text": "trop court"})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_generate_without_api_key(client: AsyncClient):
    long_offer = (
        "Ingénieur logiciel Python\nEntreprise Exemple\n"
        "Nous recherchons un ingénieur pour développer des API REST, "
        "du RAG et du déploiement Docker en environnement industriel."
    )
    with patch(
        "backend.modules.applications.service.llm.chat_json",
        new=AsyncMock(side_effect=LlmError("Clé API manquante. Ajoute OPENAI_API_KEY dans le fichier .env")),
    ):
        response = await client.post("/api/applications/generate", json={"offer_text": long_offer})
    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


@pytest.mark.asyncio
async def test_generate_success_mocked_llm(client: AsyncClient):
    long_offer = (
        "Ingénieur IA / backend\nIAS Energy\n"
        "Missions : concevoir un chatbot RAG sécurisé, APIs .NET, "
        "déploiement GPU, documentation technique, recueil de besoins métiers."
    )
    fake = {
        "job_title": "Ingénieur logiciel / IA",
        "company": "IAS Energy",
        "language": "fr",
        "fit_summary": "Le RAG IAS et le backend .NET collent à l'offre.",
        "emphasized_experiences": ["IAS RAG", "outil de configuration industrielle"],
        "cv_markdown": "# Thomas Arnaud\n\nIngénieur logiciel / IA",
        "cover_letter": "Madame, Monsieur,\n\nJe postule...",
    }
    with patch(
        "backend.modules.applications.service.llm.chat_json",
        new=AsyncMock(return_value=fake),
    ):
        response = await client.post("/api/applications/generate", json={"offer_text": long_offer})
    assert response.status_code == 200
    data = response.json()
    assert data["cv_markdown"].startswith("# Thomas")
    assert "Je postule" in data["cover_letter"]
    assert data["company"] == "IAS Energy"
    assert data["cv_pdf_base64"]
    assert data["letter_pdf_base64"]
    assert data["cv_filename"].endswith(".pdf")
    assert data["letter_filename"].endswith(".pdf")
