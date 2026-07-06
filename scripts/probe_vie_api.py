import asyncio
import json

import httpx


async def main() -> None:
    base = "https://civiweb-api-prd.azurewebsites.net/api/Offers"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://mon-vie-via.businessfrance.fr",
        "Referer": "https://mon-vie-via.businessfrance.fr/",
    }

    payloads = [
        {"specializationsIds": [24], "teletravail": 0, "porteEnv": 0, "page": 1, "pageSize": 20},
        {"specializationsIds": ["24"], "teletravail": 0, "porteEnv": 0, "page": 1, "pageSize": 20},
        {"query": "", "specializationsIds": [24], "teletravail": 0, "porteEnv": 0, "page": 1, "size": 20},
    ]

    async with httpx.AsyncClient(timeout=30, headers=headers) as client:
        for payload in payloads:
            r = await client.post(f"{base}/search", json=payload)
            print("POST", payload, "->", r.status_code)
            if r.status_code == 200:
                data = r.json()
                print(json.dumps(data, ensure_ascii=False)[:2000])
                break
            print(r.text[:300])

        r = await client.get(f"{base}/repository/search/dataset")
        print("\nDATASET", r.status_code, r.text[:500])


if __name__ == "__main__":
    asyncio.run(main())
