import re
from datetime import datetime
from html import unescape

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.core.config import settings
from backend.modules.offers.models import OfferSource, RemoteType
from backend.modules.offers.scrapers.base import OfferDetail, RawOffer, ScrapeParams, ScraperAdapter

GREENHOUSE_URL_RE = re.compile(
    r"(?:boards|job-boards)\.greenhouse\.io/(?:[^/]+/)?jobs/(\d+)|"
    r"boards\.greenhouse\.io/([^/?#]+)",
    re.I,
)


def _strip_html(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text("\n", strip=True)


def _parse_remote(location: str | None) -> RemoteType | None:
    if not location:
        return None
    lower = location.lower()
    if "remote" in lower or "télétravail" in lower or "teletravail" in lower:
        return RemoteType.REMOTE
    if "hybrid" in lower or "hybride" in lower:
        return RemoteType.HYBRID
    return RemoteType.ONSITE


class GreenhouseScraper(ScraperAdapter):
    source = OfferSource.GREENHOUSE

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._semaphore_limit = settings.ats_concurrency

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": "Grew/0.1 (personal job search tool)"},
            )
        return self._client

    def can_handle_url(self, url: str) -> bool:
        return "greenhouse.io" in url.lower()

    def _extract_slug_from_url(self, url: str) -> str | None:
        match = GREENHOUSE_URL_RE.search(url)
        if not match:
            return None
        return match.group(2) or None

    def _extract_job_id_from_url(self, url: str) -> str | None:
        match = GREENHOUSE_URL_RE.search(url)
        if match and match.group(1):
            return match.group(1)
        return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def _fetch_board(self, slug: str) -> list[dict]:
        client = await self._get_client()
        response = await client.get(
            f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
            params={"content": "true"},
        )
        response.raise_for_status()
        return response.json().get("jobs", [])

    def _job_to_raw(self, job: dict, slug: str) -> RawOffer:
        location = job.get("location", {}) or {}
        loc_name = location.get("name") if isinstance(location, dict) else str(location)
        content = job.get("content", "") or ""
        return RawOffer(
            source=self.source,
            external_id=str(job.get("id", "")),
            url=job.get("absolute_url") or f"https://boards.greenhouse.io/{slug}/jobs/{job.get('id')}",
            title=job.get("title", "Untitled"),
            company=slug.replace("-", " ").title(),
            location=loc_name,
            remote_type=_parse_remote(loc_name),
            description_raw=_strip_html(content),
            description_parsed={"departments": job.get("departments", []), "offices": job.get("offices", [])},
            posted_at=None,
        )

    async def search(self, params: ScrapeParams) -> list[RawOffer]:
        slugs = params.greenhouse_slugs
        if not slugs and params.keywords:
            return []

        results: list[RawOffer] = []
        for slug in slugs:
            try:
                jobs = await self._fetch_board(slug.strip())
            except httpx.HTTPError:
                continue
            for job in jobs[: params.max_results_per_source]:
                raw = self._job_to_raw(job, slug)
                if params.keywords:
                    kw = params.keywords.lower()
                    haystack = f"{raw.title} {raw.description_raw} {raw.company}".lower()
                    if kw not in haystack:
                        continue
                if params.location and params.location.lower() not in (raw.location or "").lower():
                    continue
                results.append(raw)
        return results

    async def fetch_detail(self, url: str) -> OfferDetail:
        job_id = self._extract_job_id_from_url(url)
        slug = self._extract_slug_from_url(url)
        if not slug:
            parts = url.rstrip("/").split("/")
            for i, part in enumerate(parts):
                if "greenhouse.io" in part and i + 1 < len(parts):
                    slug = parts[i + 1]
                    break
        if not slug:
            raise ValueError(f"Cannot parse Greenhouse URL: {url}")

        jobs = await self._fetch_board(slug)
        if job_id:
            for job in jobs:
                if str(job.get("id")) == job_id:
                    return self._job_to_raw(job, slug)
        if jobs:
            return self._job_to_raw(jobs[0], slug)
        raise ValueError(f"No job found at {url}")

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
