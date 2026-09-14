from datetime import datetime

from pydantic import BaseModel, Field

from backend.modules.applications.models import ApplicationStatus


class GenerateRequest(BaseModel):
    offer_text: str = Field(default="", max_length=40000)
    offer_id: str | None = None
    language: str | None = Field(
        default=None,
        description="fr, en, ou null pour détecter depuis l'offre",
    )
    force: bool = False


class GenerateResponse(BaseModel):
    application_id: str
    job_title: str
    company: str
    language: str
    fit_summary: str
    emphasized_experiences: list[str] = Field(default_factory=list)
    omitted_experiences: list[str] = Field(default_factory=list)
    cv_markdown: str
    cover_letter: str
    cv_pdf_base64: str
    letter_pdf_base64: str
    cv_filename: str
    letter_filename: str
    reused: bool = False
    reused_from_id: str | None = None
    reused_from_title: str | None = None
    reused_from_company: str | None = None
    status: ApplicationStatus = ApplicationStatus.DRAFT


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = None
    notes: str | None = None


class ApplicationListItem(BaseModel):
    id: str
    offer_id: str | None
    job_title: str
    company: str
    language: str
    status: ApplicationStatus
    cv_signature: str
    reused_from_id: str | None
    emphasized_experiences: list[str] = Field(default_factory=list)
    created_at: datetime
    applied_at: datetime | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


class ApplicationListResponse(BaseModel):
    items: list[ApplicationListItem]
    total: int
    page: int
    page_size: int


class ApplicationDetail(GenerateResponse):
    offer_id: str | None = None
    offer_text: str = ""
    notes: str | None = None
    created_at: datetime
    applied_at: datetime | None = None
    cv_signature: str = ""
