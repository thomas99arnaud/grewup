from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from backend.modules.offers.models import OfferSource, OfferStatus, RemoteType, ScrapeRunStatus


class ScrapeParamsSchema(BaseModel):
    sources: list[OfferSource] = Field(default_factory=lambda: [OfferSource.VIE])
    keywords: str = ""
    specialization_ids: list[str] = Field(default_factory=lambda: ["24"])
    teletravail: list[str] = Field(default_factory=lambda: ["0"])
    porte_env: list[str] = Field(default_factory=lambda: ["0"])
    location: str = ""
    greenhouse_slugs: list[str] = Field(default_factory=list)
    lever_slugs: list[str] = Field(default_factory=list)
    since: datetime | None = None
    max_results_per_source: int = 50


class OfferBase(BaseModel):
    title: str
    company: str
    url: str
    location: str | None = None
    remote_type: RemoteType | None = None
    contract_type: str | None = None
    description_raw: str = ""
    description_parsed: dict[str, Any] | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    posted_at: datetime | None = None
    notes: str | None = None


class OfferCreateManual(OfferBase):
    url: str | None = None


class OfferImportUrl(BaseModel):
    url: str


class OfferUpdate(BaseModel):
    status: OfferStatus | None = None
    notes: str | None = None
    title: str | None = None
    company: str | None = None


class OfferResponse(OfferBase):
    id: str
    source: OfferSource
    external_id: str | None
    status: OfferStatus
    compatibility_score: float | None
    scraped_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OfferListResponse(BaseModel):
    items: list[OfferResponse]
    total: int
    page: int
    page_size: int


class ScrapeRunCreate(BaseModel):
    params: ScrapeParamsSchema
    save_config_as: str | None = None


class ScrapeRunResponse(BaseModel):
    id: str
    status: ScrapeRunStatus
    params: dict[str, Any]
    offers_found: int
    offers_new: int
    offers_duplicates: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScrapeConfigCreate(BaseModel):
    name: str
    config: ScrapeParamsSchema


class ScrapeConfigResponse(BaseModel):
    id: str
    name: str
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_offers: int
    new_offers: int
    shortlisted_offers: int
    by_source: dict[str, int]
    recent_runs: list[ScrapeRunResponse]
