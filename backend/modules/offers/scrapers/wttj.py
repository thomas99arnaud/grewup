import asyncio
import json
import re
from datetime import datetime, timezone
from html import unescape
from urllib.parse import quote_plus, urljoin

import httpx
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.core.config import settings
from backend.modules.offers.models import OfferSource, RemoteType
from backend.modules.offers.scrapers.base import OfferDetail, RawOffer, ScrapeParams, ScraperAdapter

WTTJ_URL_RE = re.compile(r"welcometothejungle\.com/(?:fr/)?companies/[^/]+/jobs/([^/?#]+)", re.I)


def _parse_remote_from_text(text: str | None) -> RemoteType | None:
    if not text:
        return None
    lower = text.lower()
    if "full remote" in lower or "télétravail total" in lower or "remote" in lower:
        return RemoteType.REMOTE
    if "hybride" in lower or "hybrid" in lower:
        return RemoteType.HYBRID
    return RemoteType.ONSITE


class WttjScraper(ScraperAdapter):
    source = OfferSource.WTTJ
    BASE_URL = "https://www.welcometothejungle.com"
    API_URL = "https://www.welcometothejungle.com/api/v1/search"

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._semaphore = asyncio.Semaphore(settings.wttj_concurrency)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; Grew/0.1; personal job search)",
                    "Accept": "application/json",
                },
            )
        return self._client

    def can_handle_url(self, url: str) -> bool:
        return "welcometothejungle.com" in url.lower()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def _api_search(self, query: str, page: int = 1) -> dict:
        async with self._semaphore:
            client = await self._get_client()
            payload = {
                "query": query,
                "page": page,
                "page_size": 20,
                "sort_by": "mostRecent",
            }
            response = await client.post(self.API_URL, json=payload)
            if response.status_code == 404:
                return await self._html_search(query, page)
            response.raise_for_status()
            return response.json()

    async def _html_search(self, query: str, page: int = 1) -> dict:
        async with self._semaphore:
            client = await self._get_client()
            url = f"{self.BASE_URL}/fr/jobs?query={quote_plus(query)}&page={page}"
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            jobs = []
            for link in soup.select('a[href*="/jobs/"]'):
                href = link.get("href", "")
                if "/companies/" not in href:
                    continue
                full_url = urljoin(self.BASE_URL, href)
                title_el = link.find(["h4", "h3", "span"])
                title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)
                if title and full_url not in [j.get("url") for j in jobs]:
                    jobs.append({"url": full_url, "title": title})
            return {"jobs": jobs, "total": len(jobs)}

    def _parse_api_job(self, job: dict) -> RawOffer | None:
        try:
            slug = job.get("slug") or job.get("reference")
            org = job.get("organization", {}) or {}
            company_name = org.get("name", "Unknown")
            company_slug = org.get("slug", "")
            url = job.get("url") or (
                f"{self.BASE_URL}/fr/companies/{company_slug}/jobs/{slug}"
                if company_slug and slug
                else None
            )
            if not url:
                return None

            office = job.get("office") or {}
            location = office.get("city") or office.get("name") or job.get("location")
            remote = job.get("remote") or job.get("workplace_type")

            description = ""
            if job.get("description"):
                description = BeautifulSoup(job["description"], "lxml").get_text("\n", strip=True)

            posted_at = None
            published = job.get("published_at") or job.get("publishedAt")
            if published:
                try:
                    posted_at = datetime.fromisoformat(published.replace("Z", "+00:00"))
                except ValueError:
                    pass

            return RawOffer(
                source=self.source,
                external_id=slug or job.get("id"),
                url=url,
                title=job.get("name") or job.get("title", "Untitled"),
                company=company_name,
                location=location,
                remote_type=_parse_remote_from_text(str(remote) if remote else location),
                contract_type=job.get("contract_type") or job.get("contractType"),
                description_raw=description,
                description_parsed={"skills": job.get("skills", []), "sectors": job.get("sectors", [])},
                posted_at=posted_at,
            )
        except (KeyError, TypeError):
            return None

    async def search(self, params: ScrapeParams) -> list[RawOffer]:
        query_parts = [params.keywords, params.location]
        query = " ".join(p for p in query_parts if p).strip() or "developer"
        results: list[RawOffer] = []
        page = 1
        max_pages = max(1, params.max_results_per_source // 20)

        while page <= max_pages and len(results) < params.max_results_per_source:
            data = await self._api_search(query, page)
            jobs = data.get("jobs") or data.get("results") or []
            if not jobs:
                break

            for job in jobs:
                if isinstance(job, dict) and job.get("url") and not job.get("organization"):
                    detail = await self.fetch_detail(job["url"])
                    results.append(detail)
                else:
                    raw = self._parse_api_job(job)
                    if raw:
                        if params.since and raw.posted_at and raw.posted_at < params.since:
                            continue
                        results.append(raw)
                if len(results) >= params.max_results_per_source:
                    break
            page += 1

        return results

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def fetch_detail(self, url: str) -> OfferDetail:
        async with self._semaphore:
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            title = ""
            if soup.find("meta", property="og:title"):
                title = soup.find("meta", property="og:title")["content"]
            if not title:
                h1 = soup.find("h1")
                title = h1.get_text(strip=True) if h1 else "Untitled"

            company = ""
            company_el = soup.select_one('[data-testid="job-company-name"], a[href*="/companies/"]')
            if company_el:
                company = company_el.get_text(strip=True)

            location_el = soup.select_one('[data-testid="job-location"], [class*="location"]')
            location = location_el.get_text(strip=True) if location_el else None

            desc_el = soup.select_one(
                '[data-testid="job-description"], section[class*="description"], .job-description'
            )
            description = desc_el.get_text("\n", strip=True) if desc_el else ""

            script = soup.find("script", type="application/ld+json")
            external_id = None
            posted_at = None
            if script and script.string:
                try:
                    ld = json.loads(script.string)
                    if isinstance(ld, list):
                        ld = ld[0]
                    external_id = ld.get("identifier")
                    if ld.get("datePosted"):
                        posted_at = datetime.fromisoformat(
                            ld["datePosted"].replace("Z", "+00:00")
                        )
                    if not company and ld.get("hiringOrganization"):
                        company = ld["hiringOrganization"].get("name", "")
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass

            match = WTTJ_URL_RE.search(url)
            if match and not external_id:
                external_id = match.group(1)

            return RawOffer(
                source=self.source,
                external_id=external_id,
                url=url.split("?")[0],
                title=unescape(title),
                company=company or "Unknown",
                location=location,
                remote_type=_parse_remote_from_text(location),
                description_raw=description,
                posted_at=posted_at,
            )

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
