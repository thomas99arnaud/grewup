from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from backend.modules.offers.models import OfferSource, RemoteType


@dataclass
class ScrapeParams:
    keywords: str = ""
    location: str = ""
    greenhouse_slugs: list[str] = field(default_factory=list)
    lever_slugs: list[str] = field(default_factory=list)
    since: datetime | None = None
    max_results_per_source: int = 50


@dataclass
class RawOffer:
    source: OfferSource
    external_id: str | None
    url: str
    title: str
    company: str
    location: str | None = None
    remote_type: RemoteType | None = None
    contract_type: str | None = None
    description_raw: str = ""
    description_parsed: dict[str, Any] | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    posted_at: datetime | None = None


OfferDetail = RawOffer


class ScraperAdapter(ABC):
    source: OfferSource

    @abstractmethod
    async def search(self, params: ScrapeParams) -> list[RawOffer]:
        ...

    @abstractmethod
    async def fetch_detail(self, url: str) -> OfferDetail:
        ...

    @abstractmethod
    def can_handle_url(self, url: str) -> bool:
        ...
