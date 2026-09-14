from datetime import datetime, timezone

from sqlalchemy import Select, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.modules.applications.models import Application, ApplicationStatus
from backend.modules.applications.pdfs import render_application_pdfs


def application_payload(row: Application, *, with_pdfs: bool = True) -> dict:
    pdfs = (
        render_application_pdfs(row.cv_markdown, row.cover_letter, row.job_title, row.company)
        if with_pdfs
        else {}
    )
    return {
        "application_id": row.id,
        "offer_id": row.offer_id,
        "job_title": row.job_title,
        "company": row.company,
        "language": row.language,
        "fit_summary": row.fit_summary,
        "emphasized_experiences": list(row.emphasized_experiences or []),
        "omitted_experiences": list(row.omitted_experiences or []),
        "cv_markdown": row.cv_markdown,
        "cover_letter": row.cover_letter,
        "offer_text": row.offer_text,
        "notes": row.notes,
        "status": row.status,
        "created_at": row.created_at,
        "applied_at": row.applied_at,
        "cv_signature": row.cv_signature,
        "reused": bool(row.reused_from_id),
        "reused_from_id": row.reused_from_id,
        **pdfs,
    }


async def find_reusable(session: AsyncSession, signature: str) -> Application | None:
    result = await session.execute(
        select(Application)
        .where(Application.cv_signature == signature, Application.cv_markdown != "")
        .order_by(desc(Application.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_application(session: AsyncSession, application_id: str) -> Application | None:
    return await session.get(Application, application_id)


async def list_applications(
    session: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 50,
    status: ApplicationStatus | None = None,
    offer_id: str | None = None,
) -> tuple[list[Application], int]:
    filters = []
    if status is not None:
        filters.append(Application.status == status)
    if offer_id:
        filters.append(Application.offer_id == offer_id)
    count_stmt: Select = select(func.count()).select_from(Application)
    list_stmt: Select = select(Application)
    if filters:
        count_stmt = count_stmt.where(*filters)
        list_stmt = list_stmt.where(*filters)
    total = int((await session.execute(count_stmt)).scalar_one())
    list_stmt = (
        list_stmt.order_by(desc(Application.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = list((await session.execute(list_stmt)).scalars().all())
    return rows, total


async def save_application(
    session: AsyncSession,
    *,
    offer_id: str | None,
    company: str,
    job_title: str,
    offer_text: str,
    language: str,
    cv_markdown: str,
    cover_letter: str,
    fit_summary: str,
    emphasized_experiences: list[str],
    omitted_experiences: list[str],
    cv_signature: str,
    reused_from_id: str | None,
) -> Application:
    row = Application(
        offer_id=offer_id,
        company=company,
        job_title=job_title,
        offer_text=offer_text,
        language=language,
        cv_markdown=cv_markdown,
        cover_letter=cover_letter,
        fit_summary=fit_summary,
        emphasized_experiences=list(emphasized_experiences or []),
        omitted_experiences=list(omitted_experiences or []),
        cv_signature=cv_signature,
        reused_from_id=reused_from_id,
        status=ApplicationStatus.DRAFT,
    )
    session.add(row)
    await session.flush()
    return row


async def update_application(
    session: AsyncSession,
    row: Application,
    *,
    status: ApplicationStatus | None = None,
    notes: str | None = None,
) -> Application:
    if status is not None:
        row.status = status
        if status == ApplicationStatus.APPLIED and row.applied_at is None:
            row.applied_at = datetime.now(timezone.utc)
    if notes is not None:
        row.notes = notes
    await session.flush()
    return row
