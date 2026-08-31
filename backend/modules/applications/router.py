from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.module import BaseModule
from backend.db.session import get_session
from backend.modules.applications.llm import LlmError
from backend.modules.applications.schemas import GenerateRequest, GenerateResponse
from backend.modules.applications.service import generate_application
from backend.modules.offers.models import Offer
from backend.modules.profile.service import ProfileService

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.post("/generate", response_model=GenerateResponse)
async def generate(
    body: GenerateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GenerateResponse:
    offer_text = body.offer_text.strip()
    if body.offer_id:
        offer = await session.get(Offer, body.offer_id)
        if not offer:
            raise HTTPException(status_code=404, detail="Offre introuvable")
        if len(offer_text) < 40:
            offer_text = "\n".join(
                part
                for part in (offer.title, offer.company, offer.location or "", offer.description_raw)
                if part
            )
    if len(offer_text) < 40:
        raise HTTPException(
            status_code=400,
            detail="Colle le texte de l'offre (au moins quelques lignes) ou fournis une offre enregistrée.",
        )

    profile = await ProfileService(session).get_profile()
    try:
        result = await generate_application(offer_text, profile, body.language)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="Dépendance manquante pour lire le Word (python-docx). "
            "Dans le venv du projet : pip install python-docx",
        ) from exc
    except LlmError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not result["cv_markdown"] or not result["cover_letter"]:
        raise HTTPException(status_code=502, detail="Le modèle n'a pas renvoyé de CV et de lettre complets.")
    return GenerateResponse(**result)


class ApplicationsModule(BaseModule):
    name = "applications"

    def get_router(self) -> APIRouter:
        return router
