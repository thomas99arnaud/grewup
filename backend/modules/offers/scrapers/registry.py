from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from backend.modules.offers.models import OfferSource
from backend.modules.offers.scrapers.base import OfferDetail, RawOffer, ScraperAdapter
from backend.modules.offers.scrapers.vie import VieScraper


class ScraperRegistry:
    def __init__(self) -> None:
        self._scrapers: list[ScraperAdapter] = [VieScraper()]
        self._by_source = {s.source: s for s in self._scrapers}

    def get_by_source(self, source: OfferSource) -> ScraperAdapter | None:
        return self._by_source.get(source)

    def get_for_url(self, url: str) -> ScraperAdapter | None:
        for scraper in self._scrapers:
            if scraper.can_handle_url(url):
                return scraper
        return None

    def all_scrapers(self) -> list[ScraperAdapter]:
        return list(self._scrapers)

    async def fetch_generic(self, url: str) -> OfferDetail:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; Grew/0.1)"},
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            title = ""
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"]
            elif soup.find("h1"):
                title = soup.find("h1").get_text(strip=True)

            description = ""
            og_desc = soup.find("meta", property="og:description")
            if og_desc and og_desc.get("content"):
                description = og_desc["content"]
            else:
                main = soup.select_one("main, article, .content, #content")
                if main:
                    description = main.get_text("\n", strip=True)[:10000]

            parsed = urlparse(url)
            company = parsed.netloc.replace("www.", "").split(".")[0].title()

            return RawOffer(
                source=OfferSource.MANUAL,
                external_id=None,
                url=url.split("?")[0],
                title=title or "Untitled",
                company=company,
                description_raw=description,
            )

    async def close_all(self) -> None:
        for scraper in self._scrapers:
            if hasattr(scraper, "close"):
                await scraper.close()


scraper_registry = ScraperRegistry()
