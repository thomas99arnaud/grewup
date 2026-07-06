import json
from pathlib import Path
from unittest.mock import patch

import pytest

from backend.modules.offers.scrapers.base import ScrapeParams
from backend.modules.offers.scrapers.registry import ScraperRegistry
from backend.modules.offers.scrapers.vie import VieScraper

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def vie_search_data():
    return json.loads((FIXTURES / "vie_search.json").read_text(encoding="utf-8"))


def _make_item(offer_id: int, title: str) -> dict:
    return {
        "id": offer_id,
        "organizationName": "Acme Corp",
        "missionTitle": title,
        "cityName": "Tokyo",
        "missionDescription": "Description.",
        "missionType": "VIE",
    }


@pytest.mark.asyncio
async def test_vie_search_returns_offers(vie_search_data):
    scraper = VieScraper()

    with patch.object(scraper, "_search_page", return_value=vie_search_data):
        results = await scraper.search(
            ScrapeParams(keywords="", specialization_ids=["24"], max_results_per_source=5)
        )

    assert len(results) == 2
    assert results[0].title == "Ingénieur développement"
    assert results[0].company == "Acme Corp"
    await scraper.close()


@pytest.mark.asyncio
async def test_vie_search_paginates_until_max_results():
    scraper = VieScraper()
    pages = {
        0: {"count": 12, "result": [_make_item(i, f"Offre {i}") for i in range(1, 7)]},
        6: {"count": 12, "result": [_make_item(i, f"Offre {i}") for i in range(7, 13)]},
    }

    async def fake_search_page(payload: dict) -> dict:
        return pages[payload["skip"]]

    with patch.object(scraper, "_search_page", side_effect=fake_search_page):
        results = await scraper.search(
            ScrapeParams(specialization_ids=["24"], max_results_per_source=10)
        )

    assert len(results) == 10
    assert results[0].title == "Offre 1"
    assert results[9].title == "Offre 10"
    await scraper.close()


@pytest.mark.asyncio
async def test_vie_search_payload_uses_limit_skip():
    scraper = VieScraper()
    captured: list[dict] = []

    async def fake_search_page(payload: dict) -> dict:
        captured.append(payload)
        return {"count": 6, "result": [_make_item(1, "Offre 1")]}

    with patch.object(scraper, "_search_page", side_effect=fake_search_page):
        await scraper.search(ScrapeParams(specialization_ids=["24"], max_results_per_source=6))

    assert captured[0]["limit"] == 6
    assert captured[0]["skip"] == 0
    assert captured[0]["query"] is None
    assert captured[0]["entreprisesIds"] == [0]
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
