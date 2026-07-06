import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.modules.offers.scrapers.base import ScrapeParams
from backend.modules.offers.scrapers.registry import ScraperRegistry
from backend.modules.offers.scrapers.vie import VieScraper

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def vie_search_data():
    return json.loads((FIXTURES / "vie_search.json").read_text(encoding="utf-8"))


@pytest.mark.asyncio
async def test_vie_search_returns_offers(vie_search_data):
    scraper = VieScraper()
    mock_response = AsyncMock()
    mock_response.raise_for_status = lambda: None
    mock_response.json = lambda: vie_search_data

    with patch.object(scraper, "_search_page", return_value=vie_search_data):
        results = await scraper.search(
            ScrapeParams(keywords="", specialization_ids=["24"], max_results_per_source=5)
        )

    assert len(results) == 2
    assert results[0].title == "Ingénieur développement"
    assert results[0].company == "Acme Corp"
    assert results[0].url.startswith("https://mon-vie-via.businessfrance.fr/offres/")
    await scraper.close()


@pytest.mark.asyncio
async def test_vie_fetch_detail(vie_search_data):
    scraper = VieScraper()
    item = vie_search_data["result"][0]

    with patch.object(scraper, "_fetch_details", return_value=item):
        detail = await scraper.fetch_detail("https://mon-vie-via.businessfrance.fr/offres/12345")

    assert detail.external_id == "12345"
    assert detail.title == "Ingénieur développement"
    await scraper.close()


def test_registry_detects_vie_url():
    registry = ScraperRegistry()
    scraper = registry.get_for_url("https://mon-vie-via.businessfrance.fr/offres/999")
    assert scraper is not None
    assert scraper.source.value == "vie"


def test_registry_only_vie_scraper():
    registry = ScraperRegistry()
    scrapers = registry.all_scrapers()
    assert len(scrapers) == 1
    assert scrapers[0].source.value == "vie"
