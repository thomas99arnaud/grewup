import re
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.modules.offers.models import OfferSource
from backend.modules.offers.scrapers.base import OfferDetail, RawOffer, ScrapeParams, ScraperAdapter

API_BASE = "https://civiweb-api-prd.azurewebsites.net/api/Offers"
SITE_BASE = "https://mon-vie-via.businessfrance.fr"
API_PAGE_SIZE = 6
VIE_URL_RE = re.compile(
    r"mon-vie-via\.businessfrance\.fr/offres/(\d+)",
    re.I,
)


class VieScraper(ScraperAdapter):
    source = OfferSource.VIE

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (compatible; Grew/0.1; personal job search)",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": SITE_BASE,
            "Referer": f"{SITE_BASE}/",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=45.0, headers=self._headers())
        return self._client

    def can_handle_url(self, url: str) -> bool:
        return "mon-vie-via.businessfrance.fr" in url.lower() or "businessfrance.fr/offres" in url.lower()

    def _extract_id(self, url: str) -> str | None:
        match = VIE_URL_RE.search(url)
        return match.group(1) if match else None

    def _item_to_raw(self, item: dict[str, Any]) -> RawOffer | None:
        offer_id = item.get("id")
        if not offer_id:
            return None

        org = (item.get("organizationName") or "").strip()
        title = (item.get("missionTitle") or "Sans titre").strip()
        city = (item.get("cityName") or item.get("cityNameEn") or "").strip() or None
        mission_type = item.get("missionType") or item.get("missionTypeEn")

        description_parts = [
            item.get("missionDescription") or "",
            item.get("organizationPresentation") or "",
        ]
        description = "\n\n".join(p.strip() for p in description_parts if p and str(p).strip())

        return RawOffer(
            source=self.source,
            external_id=str(offer_id),
            url=f"{SITE_BASE}/offres/{offer_id}",
            title=title,
            company=org or "Entreprise VIE",
            location=city,
            contract_type=str(mission_type) if mission_type else "VIE",
            description_raw=description,
            description_parsed={
                "mission_duration_months": item.get("missionDuration"),
                "mission_type": mission_type,
                "specialization": item.get("specialization"),
                "country": item.get("countryName") or item.get("countryNameEn"),
            },
        )

    def _build_search_payload(self, params: ScrapeParams, skip: int, limit: int) -> dict[str, Any]:
        query = params.keywords.strip() if params.keywords else None
        return {
            "limit": limit,
            "skip": skip,
            "query": query,
            "specializationsIds": params.specialization_ids or ["24"],
            "teletravail": params.teletravail or ["0"],
            "porteEnv": params.porte_env or ["0"],
            "activitySectorId": [],
            "companiesSizes": [],
            "countriesIds": [],
            "entreprisesIds": [0],
            "geographicZones": [],
            "missionStartDate": None,
            "missionsDurations": [],
            "missionsTypesIds": [],
            "studiesLevelId": [],
        }

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def _search_page(self, payload: dict[str, Any]) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.post(f"{API_BASE}/search", json=payload)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def _fetch_details(self, offer_id: str) -> dict[str, Any]:
        client = await self._get_client()
        response = await client.get(f"{API_BASE}/details/{offer_id}")
        response.raise_for_status()
        return response.json()

    async def search(self, params: ScrapeParams) -> list[RawOffer]:
        results: list[RawOffer] = []
        seen_ids: set[str] = set()
        skip = 0
        limit = API_PAGE_SIZE
        total_count: int | None = None

        while len(results) < params.max_results_per_source:
            data = await self._search_page(self._build_search_payload(params, skip, limit))
            if total_count is None and data.get("count") is not None:
                total_count = int(data["count"])

            items = data.get("result") or []
            if not items:
                break

            for item in items:
                raw = self._item_to_raw(item)
                if not raw or raw.external_id in seen_ids:
                    continue
                seen_ids.add(raw.external_id)
                results.append(raw)
                if len(results) >= params.max_results_per_source:
                    break

            if total_count is not None and skip + limit >= total_count:
                break
            if len(items) < limit:
                break
            skip += limit

        return results

    async def fetch_detail(self, url: str) -> OfferDetail:
        offer_id = self._extract_id(url)
        if not offer_id:
            raise ValueError(f"Cannot parse VIE offer URL: {url}")

        item = await self._fetch_details(offer_id)
        raw = self._item_to_raw(item)
        if not raw:
            raise ValueError(f"No offer found for id {offer_id}")
        return raw

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
