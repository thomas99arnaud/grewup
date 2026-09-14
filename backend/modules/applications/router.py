from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.module import BaseModule
from backend.db.session import get_session
from backend.modules.applications.llm import LlmError
from backend.modules.applications.models import Application, ApplicationStatus
from backend.modules.applications.schemas import (
    ApplicationDetail,
    ApplicationListItem,
    ApplicationListResponse,
    ApplicationUpdate,
    GenerateRequest,
    GenerateResponse,
)
from backend.modules.applications.service import generate_application, generate_letter_only
from backend.modules.applications.signature import (
    block_labels,
    cv_signature,
    detect_language,
    omitted_labels,
    select_blocks,
)
from backend.modules.applications.pdfs import order_cv_text
from backend.modules.applications.store import (
    application_payload,
    find_reusable,
    get_application,
    list_applications,
    save_application,
    update_application,
)
from backend.modules.offers.models import Offer
from backend.modules.profile.service import ProfileService

router = APIRouter(prefix="/api/applications", tags=["applications"])


def _to_generate_response(row: Application, extra: dict | None = None) -> GenerateResponse:
    data = application_payload(row, with_pdfs=True)
    if extra:
        data.update(extra)
    return GenerateResponse(**data)


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

    language = detect_language(offer_text, body.language)
    signature = cv_signature(offer_text, language)
    previous = None if body.force else await find_reusable(session, signature)

    profile = await ProfileService(session).get_profile()
    reused_from_title = None
    reused_from_company = None
    reused_from_id = None
    try:
        if previous:
            result = await generate_letter_only(offer_text, previous.cv_markdown, language)
            result["emphasized_experiences"] = list(previous.emphasized_experiences or [])
            result["omitted_experiences"] = list(previous.omitted_experiences or [])
            reused_from_id = previous.id
            reused_from_title = previous.job_title
            reused_from_company = previous.company
        else:
            result = await generate_application(offer_text, profile, language)
            blocks = select_blocks(offer_text)
            if not result.get("emphasized_experiences"):
                result["emphasized_experiences"] = block_labels(blocks)
            if not result.get("omitted_experiences"):
                result["omitted_experiences"] = omitted_labels(blocks)
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

    row = await save_application(
        session,
        offer_id=body.offer_id,
        company=str(result.get("company") or ""),
        job_title=str(result.get("job_title") or ""),
        offer_text=offer_text,
        language=str(result.get("language") or language),
        cv_markdown=str(result["cv_markdown"]),
        cover_letter=str(result["cover_letter"]),
        fit_summary=str(result.get("fit_summary") or ""),
        emphasized_experiences=list(result.get("emphasized_experiences") or []),
        omitted_experiences=list(result.get("omitted_experiences") or []),
        cv_signature=signature,
        reused_from_id=reused_from_id,
    )
    return _to_generate_response(
        row,
        extra={
            "cv_pdf_base64": result["cv_pdf_base64"],
            "letter_pdf_base64": result["letter_pdf_base64"],
            "cv_filename": result["cv_filename"],
            "letter_filename": result["letter_filename"],
            "reused_from_title": reused_from_title,
            "reused_from_company": reused_from_company,
        },
    )


@router.get("", response_model=ApplicationListResponse)
async def list_saved(
    session: Annotated[AsyncSession, Depends(get_session)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: ApplicationStatus | None = None,
    offer_id: str | None = None,
) -> ApplicationListResponse:
    rows, total = await list_applications(
        session, page=page, page_size=page_size, status=status, offer_id=offer_id
    )
    return ApplicationListResponse(
        items=[ApplicationListItem.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{application_id}", response_model=ApplicationDetail)
async def get_saved(
    application_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ApplicationDetail:
    row = await get_application(session, application_id)
    if not row:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    data = application_payload(row, with_pdfs=True)
    extra: dict = {}
    if row.reused_from_id:
        source = await get_application(session, row.reused_from_id)
        if source:
            extra["reused_from_title"] = source.job_title
            extra["reused_from_company"] = source.company
    data.update(extra)
    return ApplicationDetail(**data)


@router.patch("/{application_id}", response_model=ApplicationDetail)
async def patch_saved(
    application_id: str,
    body: ApplicationUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ApplicationDetail:
    row = await get_application(session, application_id)
    if not row:
        raise HTTPException(status_code=404, detail="Candidature introuvable")
    row = await update_application(
        session,
        row,
        status=body.status,
        notes=body.notes,
        cv_markdown=order_cv_text(body.cv_markdown) if body.cv_markdown is not None else None,
        cover_letter=body.cover_letter,
    )
    data = application_payload(row, with_pdfs=True)
    extra: dict = {}
    if row.reused_from_id:
        source = await get_application(session, row.reused_from_id)
        if source:
            extra["reused_from_title"] = source.job_title
            extra["reused_from_company"] = source.company
    data.update(extra)
    return ApplicationDetail(**data)


class ApplicationsModule(BaseModule):
    name = "applications"

    def get_router(self) -> APIRouter:
        return router
