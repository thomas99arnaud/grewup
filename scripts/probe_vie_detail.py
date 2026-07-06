import asyncio
import json

from playwright.async_api import async_playwright


async def main() -> None:
    api_calls: list[str] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        async def on_response(response) -> None:
            url = response.url
            if "civiweb-api" in url and response.status == 200:
                api_calls.append(url)

        page.on("response", on_response)
        await page.goto(
            "https://mon-vie-via.businessfrance.fr/offres/recherche?query&specializationsIds=24&teletravail=0&porteEnv=0",
            wait_until="networkidle",
            timeout=90000,
        )
        await page.wait_for_timeout(3000)

        # click first offer link if exists
        offer_links = await page.eval_on_selector_all(
            "a[href*='/offres/']",
            "els => els.map(e => e.href).filter(h => /\\/offres\\/\\d+/.test(h))",
        )
        print("OFFER_LINKS", offer_links[:5])

        if offer_links:
            await page.goto(offer_links[0], wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(2000)

        print("API after detail:")
        for u in api_calls:
            if u not in api_calls[:10]:
                print(u)
        for u in api_calls[-15:]:
            print(u)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
