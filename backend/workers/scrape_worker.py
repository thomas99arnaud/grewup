from datetime import datetime

from arq import create_pool
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.db.session import async_session_factory
from backend.modules.offers.models import OfferSource
from backend.modules.offers.scrapers.base import ScrapeParams
from backend.modules.offers.service import OfferService


def _parse_redis_settings() -> RedisSettings:
    url = settings.redis_url
    if url.startswith("redis://"):
        url = url[8:]
    host, _, port_db = url.partition(":")
    port = 6379
    db = 0
    if port_db:
        port_str, _, db_str = port_db.partition("/")
        if port_str:
            port = int(port_str)
        if db_str:
            db = int(db_str)
    return RedisSettings(host=host or "localhost", port=port, database=db)


async def enqueue_scrape_run(run_id: str, params_dict: dict, sources: list[str]) -> bool:
    if not settings.use_arq_worker:
        return False
    try:
        redis = await create_pool(_parse_redis_settings())
        await redis.enqueue_job("run_scrape_job", run_id, params_dict, sources)
        await redis.close()
        return True
    except Exception:
        return False


async def run_scrape_job(ctx: dict, run_id: str, params_dict: dict, sources: list[str]) -> None:
    scrape_params = ScrapeParams(
        keywords=params_dict.get("keywords", ""),
        location=params_dict.get("location", ""),
        greenhouse_slugs=params_dict.get("greenhouse_slugs", []),
        lever_slugs=params_dict.get("lever_slugs", []),
        max_results_per_source=params_dict.get("max_results_per_source", 50),
    )
    if params_dict.get("since"):
        scrape_params.since = datetime.fromisoformat(params_dict["since"])

    source_enums = [OfferSource(s) for s in sources]

    async with async_session_factory() as session:
        service = OfferService(session)
        await service.run_scrape(run_id, scrape_params, source_enums)


class WorkerSettings:
    functions = [run_scrape_job]
    redis_settings = _parse_redis_settings()
