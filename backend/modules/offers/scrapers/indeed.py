import asyncio
import re
from datetime import datetime
from urllib.parse import quote_plus, urljoin

from bs4 import BeautifulSoup
from playwright.async_api import Browser, async_playwright
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.core.config import settings
from backend.modules.offers.models import OfferSource, RemoteType
from backend.modules.offers.scrapers.base import OfferDetail, RawOffer, ScrapeParams, ScraperAdapter

INDEED_URL_RE = re.compile(r"indeed\.(?:com|fr).*?[?&]jk=([a-z0-9]+)", re.I)


class IndeedScraper(ScraperAdapter):
    source = OfferSource.INDEED
    BASE_URL = "https://fr.indeed.com"

    def __init__(self) -> None:
        self._browser: Browser | None = None
        self._playwright = None
        self._semaphore = asyncio.Semaphore(settings.indeed_concurrency)
        self._last_request = 0.0

    async def _ensure_browser(self) -> Browser:
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
        return self._browser

    def can_handle_url(self, url: str) -> bool:
        return "indeed." in url.lower()

    async def _rate_limit(self) -> None:
        import time

        async with self._semaphore:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < settings.indeed_delay_seconds:
                await asyncio.sleep(settings.indeed_delay_seconds - elapsed)
            self._last_request = time.monotonic()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=2, min=2, max=10))
    async def _fetch_page(self, url: str) -> str:
        await self._rate_limit()
        browser = await self._ensure_browser()
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="fr-FR",
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2000)
            content = await page.content()
            return content
        finally:
            await context.close()

    def _parse_search_results(self, html: str) -> list[RawOffer]:
        soup = BeautifulSoup(html, "lxml")
        results: list[RawOffer] = []

        cards = soup.select("div.job_seen_beacon, div.jobsearch-ResultsList > li, .result")
        for card in cards:
            link = card.select_one("a[href*='/viewjob'], a[href*='jk='], h2.jobTitle a")
            if not link:
                continue
            href = link.get("href", "")
            job_url = urljoin(self.BASE_URL, href)
            jk_match = INDEED_URL_RE.search(job_url)
            external_id = jk_match.group(1) if jk_match else None

            title_el = card.select_one("h2.jobTitle span, h2 span, .jobTitle")
            title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)

            company_el = card.select_one('[data-testid="company-name"], .companyName, span.company')
            company = company_el.get_text(strip=True) if company_el else "Unknown"

            location_el = card.select_one('[data-testid="text-location"], .companyLocation')
            location = location_el.get_text(strip=True) if location_el else None

            if title and job_url:
                results.append(
                    RawOffer(
                        source=self.source,
                        external_id=external_id,
                        url=job_url,
                        title=title,
                        company=company,
                        location=location,
                        remote_type=None,
                        description_raw="",
                    )
                )
        return results

    def _parse_job_detail(self, html: str, url: str) -> OfferDetail:
        soup = BeautifulSoup(html, "lxml")
        jk_match = INDEED_URL_RE.search(url)
        external_id = jk_match.group(1) if jk_match else None

        title_el = soup.select_one("h1.jobsearch-JobInfoHeader-title, h1")
        title = title_el.get_text(strip=True) if title_el else "Untitled"

        company_el = soup.select_one(
            '[data-testid="inlineHeader-companyName"], [data-company-name="true"], .jobsearch-InlineCompanyRating a'
        )
        company = company_el.get_text(strip=True) if company_el else "Unknown"

        location_el = soup.select_one(
            '[data-testid="job-location"], div[data-testid="inlineHeader-companyLocation"]'
        )
        location = location_el.get_text(strip=True) if location_el else None

        desc_el = soup.select_one("#jobDescriptionText, .jobsearch-jobDescriptionText")
        description = desc_el.get_text("\n", strip=True) if desc_el else ""

        return RawOffer(
            source=self.source,
            external_id=external_id,
            url=url.split("?")[0] if "?" in url else url,
            title=title,
            company=company,
            location=location,
            remote_type=RemoteType.ONSITE,
            description_raw=description,
        )

    async def search(self, params: ScrapeParams) -> list[RawOffer]:
        query = params.keywords or "developer"
        location = params.location or "France"
        url = (
            f"{self.BASE_URL}/jobs?q={quote_plus(query)}"
            f"&l={quote_plus(location)}&sort=date"
        )

        try:
            html = await self._fetch_page(url)
            results = self._parse_search_results(html)
        except Exception:
            return []

        detailed: list[RawOffer] = []
        for raw in results[: params.max_results_per_source]:
            if raw.url and not raw.description_raw:
                try:
                    detail = await self.fetch_detail(raw.url)
                    detailed.append(detail)
                except Exception:
                    detailed.append(raw)
            else:
                detailed.append(raw)
        return detailed

    async def fetch_detail(self, url: str) -> OfferDetail:
        if "viewjob" not in url and "jk=" not in url:
            jk = INDEED_URL_RE.search(url)
            if not jk:
                raise ValueError(f"Cannot parse Indeed URL: {url}")
            url = f"{self.BASE_URL}/viewjob?jk={jk.group(1)}"
        html = await self._fetch_page(url)
        return self._parse_job_detail(html, url)

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
