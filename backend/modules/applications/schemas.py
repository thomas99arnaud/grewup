from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    offer_text: str = Field(default="", max_length=40000)
    offer_id: str | None = None
    language: str | None = Field(
        default=None,
        description="fr, en, ou null pour détecter depuis l'offre",
    )


class GenerateResponse(BaseModel):
    job_title: str
    company: str
    language: str
    fit_summary: str
    emphasized_experiences: list[str] = Field(default_factory=list)
    cv_markdown: str
    cover_letter: str
    cv_pdf_base64: str
    letter_pdf_base64: str
    cv_filename: str
    letter_filename: str
