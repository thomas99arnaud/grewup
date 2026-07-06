import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.events import event_bus
from backend.modules.offers.models import (
    Offer,
    OfferSource,
    OfferStatus,
    ScrapeConfig,
    ScrapeRun,
    ScrapeRunStatus,
)
from backend.modules.offers.scrapers.base import RawOffer, ScrapeParams
from backend.modules.offers.scrapers.registry import scraper_registry


class OfferService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_offers(
        self,
        page: int = 1,
        page_size: int = 20,
        source: OfferSource | None = None,
        status: OfferStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[Offer], int]:
        query = select(Offer).where(Offer.status != OfferStatus.ARCHIVED)
        count_query = select(func.count()).select_from(Offer).where(Offer.status != OfferStatus.ARCHIVED)

        if source:
            query = query.where(Offer.source == source)
            count_query = count_query.where(Offer.source == source)
        if status:
            query = query.where(Offer.status == status)
            count_query = count_query.where(Offer.status == status)
        if search:
            pattern = f"%{search}%"
            search_filter = or_(
                Offer.title.ilike(pattern),
                Offer.company.ilike(pattern),
                Offer.description_raw.ilike(pattern),
                Offer.location.ilike(pattern),
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        total = (await self.session.execute(count_query)).scalar() or 0
        query = query.order_by(Offer.scraped_at.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list((await self.session.execute(query)).scalars().all())
        return items, total

    async def get_offer(self, offer_id: str) -> Offer | None:
        return await self.session.get(Offer, offer_id)

    async def update_offer(self, offer_id: str, **fields) -> Offer | None:
        offer = await self.get_offer(offer_id)
        if not offer:
            return None
        for key, value in fields.items():
            if value is not None and hasattr(offer, key):
                setattr(offer, key, value)
        await self.session.flush()
        return offer

    async def archive_offer(self, offer_id: str) -> bool:
        offer = await self.update_offer(offer_id, status=OfferStatus.ARCHIVED)
        return offer is not None

    async def _is_duplicate(self, raw: RawOffer) -> bool:
        if raw.url:
            existing = await self.session.execute(select(Offer).where(Offer.url == raw.url))
            if existing.scalar_one_or_none():
                return True
        if raw.external_id and raw.source:
            existing = await self.session.execute(
                select(Offer).where(
                    Offer.source == raw.source,
                    Offer.external_id == raw.external_id,
                )
            )
            if existing.scalar_one_or_none():
                return True
        return False

    async def upsert_raw_offer(self, raw: RawOffer) -> tuple[Offer | None, bool]:
        if await self._is_duplicate(raw):
            return None, True

        offer = Offer(
            id=str(uuid.uuid4()),
            source=raw.source,
            external_id=raw.external_id,
            url=raw.url,
            title=raw.title,
            company=raw.company,
            location=raw.location,
            remote_type=raw.remote_type,
            contract_type=raw.contract_type,
            description_raw=raw.description_raw or "",
            description_parsed=raw.description_parsed or {},
            salary_min=raw.salary_min,
            salary_max=raw.salary_max,
            salary_currency=raw.salary_currency,
            posted_at=raw.posted_at,
            scraped_at=datetime.now(timezone.utc),
            status=OfferStatus.NEW,
        )
        self.session.add(offer)
        await self.session.flush()
        await event_bus.emit("offer.created", offer_id=offer.id)
        return offer, False

    async def create_manual(self, data: dict) -> Offer:
        url = data.get("url") or f"manual://{uuid.uuid4()}"
        raw = RawOffer(
            source=OfferSource.MANUAL,
            external_id=None,
            url=url,
            title=data["title"],
            company=data["company"],
            location=data.get("location"),
            remote_type=data.get("remote_type"),
            contract_type=data.get("contract_type"),
            description_raw=data.get("description_raw", ""),
            description_parsed=data.get("description_parsed"),
            salary_min=data.get("salary_min"),
            salary_max=data.get("salary_max"),
            salary_currency=data.get("salary_currency"),
            posted_at=data.get("posted_at"),
        )
        if data.get("url") and await self._is_duplicate(raw):
            existing = (
                await self.session.execute(select(Offer).where(Offer.url == url))
            ).scalar_one()
            return existing

        offer, _ = await self.upsert_raw_offer(raw)
        if offer and data.get("notes"):
            offer.notes = data["notes"]
        return offer  # type: ignore[return-value]

    async def import_from_url(self, url: str) -> Offer:
        scraper = scraper_registry.get_for_url(url)
        if scraper:
            detail = await scraper.fetch_detail(url)
        else:
            detail = await scraper_registry.fetch_generic(url)
            detail.source = OfferSource.MANUAL

        offer, is_dup = await self.upsert_raw_offer(detail)
        if is_dup:
            existing = (
                await self.session.execute(select(Offer).where(Offer.url == detail.url))
            ).scalar_one()
            return existing
        return offer  # type: ignore[return-value]

    async def run_scrape(self, run_id: str, params: ScrapeParams, sources: list[OfferSource]) -> None:
        run = await self.session.get(ScrapeRun, run_id)
        if not run:
            return

        run.status = ScrapeRunStatus.RUNNING
        run.started_at = datetime.now(timezone.utc)
        await self.session.commit()

        found = 0
        new_count = 0
        dup_count = 0
        error_msg: str | None = None

        try:
            for source in sources:
                scraper = scraper_registry.get_by_source(source)
                if not scraper:
                    continue
                raw_offers = await scraper.search(params)
                found += len(raw_offers)
                for raw in raw_offers:
                    offer, is_dup = await self.upsert_raw_offer(raw)
                    if is_dup:
                        dup_count += 1
                    else:
                        new_count += 1
                await self.session.commit()

            run.status = ScrapeRunStatus.DONE
        except Exception as exc:
            run.status = ScrapeRunStatus.FAILED
            error_msg = str(exc)
        finally:
            run.offers_found = found
            run.offers_new = new_count
            run.offers_duplicates = dup_count
            run.error_message = error_msg
            run.completed_at = datetime.now(timezone.utc)
            await self.session.commit()
            await scraper_registry.close_all()

    async def create_scrape_run(self, params: dict, sources: list[OfferSource]) -> ScrapeRun:
        run = ScrapeRun(
            id=str(uuid.uuid4()),
            status=ScrapeRunStatus.PENDING,
            params={**params, "sources": [s.value for s in sources]},
        )
        self.session.add(run)
        await self.session.flush()
        return run

    async def get_scrape_run(self, run_id: str) -> ScrapeRun | None:
        return await self.session.get(ScrapeRun, run_id)

    async def list_scrape_runs(self, limit: int = 20) -> list[ScrapeRun]:
        result = await self.session.execute(
            select(ScrapeRun).order_by(ScrapeRun.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def create_scrape_config(self, name: str, config: dict) -> ScrapeConfig:
        cfg = ScrapeConfig(id=str(uuid.uuid4()), name=name, config=config)
        self.session.add(cfg)
        await self.session.flush()
        return cfg

    async def list_scrape_configs(self) -> list[ScrapeConfig]:
        result = await self.session.execute(
            select(ScrapeConfig).order_by(ScrapeConfig.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_dashboard_stats(self) -> dict:
        total = (await self.session.execute(select(func.count()).select_from(Offer))).scalar() or 0
        new_count = (
            await self.session.execute(
                select(func.count()).select_from(Offer).where(Offer.status == OfferStatus.NEW)
            )
        ).scalar() or 0
        shortlisted = (
            await self.session.execute(
                select(func.count())
                .select_from(Offer)
                .where(Offer.status == OfferStatus.SHORTLISTED)
            )
        ).scalar() or 0

        by_source_result = await self.session.execute(
            select(Offer.source, func.count()).group_by(Offer.source)
        )
        by_source = {row[0].value: row[1] for row in by_source_result.all()}
        recent_runs = await self.list_scrape_runs(limit=5)

        return {
            "total_offers": total,
            "new_offers": new_count,
            "shortlisted_offers": shortlisted,
            "by_source": by_source,
            "recent_runs": recent_runs,
        }
