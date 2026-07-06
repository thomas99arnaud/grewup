import re

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.core.config import settings
from backend.modules.offers.models import OfferSource, RemoteType
from backend.modules.offers.scrapers.base import OfferDetail, RawOffer, ScrapeParams, ScraperAdapter

LEVER_URL_RE = re.compile(r"jobs\.lever\.co/([^/?#]+)(?:/([a-f0-9-]+))?", re.I)


def _parse_remote(workplace_type: str | None, location: str | None) -> RemoteType | None:
    wt = (workplace_type or "").lower()
    if wt == "remote" or (location and "remote" in location.lower()):
        return RemoteType.REMOTE
    if wt == "hybrid":
        return RemoteType.HYBRID
    if wt or location:
        return RemoteType.ONSITE
    return None


class LeverScraper(ScraperAdapter):
    source = OfferSource.LEVER

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={"User-Agent": "Grew/0.1 (personal job search tool)"},
            )
        return self._client

    def can_handle_url(self, url: str) -> bool:
        return "lever.co" in url.lower()

    def _parse_url(self, url: str) -> tuple[str | None, str | None]:
        match = LEVER_URL_RE.search(url)
        if not match:
            return None, None
        return match.group(1), match.group(2)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def _fetch_postings(self, slug: str) -> list[dict]:
        client = await self._get_client()
        response = await client.get(
            f"https://api.lever.co/v0/postings/{slug}",
            params={"mode": "json"},
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []

    def _posting_to_raw(self, posting: dict, slug: str) -> RawOffer:
        categories = posting.get("categories", {}) or {}
        location = categories.get("location")
        commitment = categories.get("commitment")
        description = posting.get("descriptionPlain") or posting.get("description", "") or ""
        lists = posting.get("lists", []) or []
        extra = "\n".join(
            f"{item.get('text', '')}\n" + "\n".join(item.get("content", "").split("\n"))
            for item in lists
        )
        full_desc = f"{description}\n{extra}".strip()
        workplace = posting.get("workplaceType")

        created_at = posting.get("createdAt")
        posted_at = None
        if created_at:
            from datetime import datetime, timezone

            posted_at = datetime.fromtimestamp(created_at / 1000, tz=timezone.utc)

        return RawOffer(
            source=self.source,
            external_id=posting.get("id"),
            url=posting.get("hostedUrl") or f"https://jobs.lever.co/{slug}/{posting.get('id')}",
            title=posting.get("text", "Untitled"),
            company=posting.get("company") or slug.replace("-", " ").title(),
            location=location,
            remote_type=_parse_remote(workplace, location),
            contract_type=commitment,
            description_raw=full_desc,
            description_parsed={"categories": categories, "workplace_type": workplace},
            posted_at=posted_at,
        )

    async def search(self, params: ScrapeParams) -> list[RawOffer]:
        results: list[RawOffer] = []
        for slug in params.lever_slugs:
            try:
                postings = await self._fetch_postings(slug.strip())
            except httpx.HTTPError:
                continue
            for posting in postings[: params.max_results_per_source]:
                raw = self._posting_to_raw(posting, slug)
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
        slug, posting_id = self._parse_url(url)
        if not slug:
            raise ValueError(f"Cannot parse Lever URL: {url}")
        postings = await self._fetch_postings(slug)
        if posting_id:
            for posting in postings:
                if posting.get("id") == posting_id:
                    return self._posting_to_raw(posting, slug)
        if postings:
            return self._posting_to_raw(postings[0], slug)
        raise ValueError(f"No posting found at {url}")

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
