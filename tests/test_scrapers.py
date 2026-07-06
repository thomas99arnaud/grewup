import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from backend.modules.offers.scrapers.base import ScrapeParams
from backend.modules.offers.scrapers.greenhouse import GreenhouseScraper
from backend.modules.offers.scrapers.lever import LeverScraper
from backend.modules.offers.scrapers.registry import ScraperRegistry

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def greenhouse_data():
    return json.loads((FIXTURES / "greenhouse_jobs.json").read_text())


@pytest.fixture
def lever_data():
    return json.loads((FIXTURES / "lever_postings.json").read_text())


@pytest.mark.asyncio
async def test_greenhouse_search_filters_by_keyword(greenhouse_data):
    scraper = GreenhouseScraper()
    mock_response = AsyncMock()
    mock_response.raise_for_status = AsyncMock()
    mock_response.json = lambda: greenhouse_data

    with patch.object(scraper, "_fetch_board", return_value=greenhouse_data["jobs"]):
        results = await scraper.search(
            ScrapeParams(keywords="Python", greenhouse_slugs=["acme"])
        )
    assert len(results) == 1
    assert results[0].title == "Senior Backend Engineer"
    assert results[0].company == "Acme"
    await scraper.close()


@pytest.mark.asyncio
async def test_greenhouse_search_excludes_non_matching(greenhouse_data):
    scraper = GreenhouseScraper()
    with patch.object(scraper, "_fetch_board", return_value=greenhouse_data["jobs"]):
        results = await scraper.search(
            ScrapeParams(keywords="Java", greenhouse_slugs=["acme"])
        )
    assert len(results) == 0
    await scraper.close()


@pytest.mark.asyncio
async def test_lever_search(lever_data):
    scraper = LeverScraper()
    with patch.object(scraper, "_fetch_postings", return_value=lever_data):
        results = await scraper.search(
            ScrapeParams(keywords="Python", lever_slugs=["acme"])
        )
    assert len(results) == 1
    assert results[0].company == "Acme Corp"
    await scraper.close()


def test_registry_detects_greenhouse_url():
    registry = ScraperRegistry()
    scraper = registry.get_for_url("https://boards.greenhouse.io/stripe/jobs/123")
    assert scraper is not None
    assert scraper.source.value == "greenhouse"


def test_registry_detects_lever_url():
    registry = ScraperRegistry()
    scraper = registry.get_for_url("https://jobs.lever.co/netflix/abc-123")
    assert scraper is not None
    assert scraper.source.value == "lever"


def test_registry_detects_wttj_url():
    registry = ScraperRegistry()
    scraper = registry.get_for_url(
        "https://www.welcometothejungle.com/fr/companies/foo/jobs/bar"
    )
    assert scraper is not None
    assert scraper.source.value == "wttj"
