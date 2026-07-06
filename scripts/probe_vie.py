import asyncio
import json

from playwright.async_api import async_playwright


async def main() -> None:
    api_calls: list[tuple[str, int, str]] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        async def on_response(response) -> None:
            url = response.url
            if any(k in url.lower() for k in ("api", "offre", "graphql", "search")):
                ct = response.headers.get("content-type", "")
                api_calls.append((url, response.status, ct))

        page.on("response", on_response)
        await page.goto(
            "https://mon-vie-via.businessfrance.fr/offres/recherche?query&specializationsIds=24&teletravail=0&porteEnv=0",
            wait_until="networkidle",
            timeout=90000,
        )
        await page.wait_for_timeout(5000)

        links = await page.eval_on_selector_all(
            "a",
            "els => els.filter(e => e.href && e.href.includes('offre')).map(e => ({href: e.href, text: (e.innerText||'').trim().slice(0,100)}))",
        )
        print("LINKS_COUNT", len(links))
        for link in links[:10]:
            print(json.dumps(link, ensure_ascii=False))

        print("\nAPI_CALLS:")
        for url, status, ct in api_calls:
            print(status, ct[:40], url)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
