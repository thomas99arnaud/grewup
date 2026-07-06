import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.module import BaseModule
from backend.db.session import get_session
from backend.modules.offers.models import OfferSource, OfferStatus
from backend.modules.offers.schemas import (
    DashboardStats,
    OfferCreateManual,
    OfferImportUrl,
    OfferListResponse,
    OfferResponse,
    OfferUpdate,
    ScrapeConfigCreate,
    ScrapeConfigResponse,
    ScrapeRunCreate,
    ScrapeRunResponse,
)
from backend.modules.offers.scrapers.base import ScrapeParams
from backend.modules.offers.service import OfferService
from backend.workers.scrape_worker import enqueue_scrape_run

router = APIRouter(prefix="/api", tags=["offers"])


def get_offer_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> OfferService:
    return OfferService(session)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(service: Annotated[OfferService, Depends(get_offer_service)]) -> DashboardStats:
    stats = await service.get_dashboard_stats()
    return DashboardStats(
        total_offers=stats["total_offers"],
        new_offers=stats["new_offers"],
        shortlisted_offers=stats["shortlisted_offers"],
        by_source=stats["by_source"],
        recent_runs=[ScrapeRunResponse.model_validate(r) for r in stats["recent_runs"]],
    )


@router.get("/offers", response_model=OfferListResponse)
async def list_offers(
    service: Annotated[OfferService, Depends(get_offer_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    source: OfferSource | None = None,
    status: OfferStatus | None = None,
    search: str | None = None,
) -> OfferListResponse:
    items, total = await service.list_offers(page, page_size, source, status, search)
    return OfferListResponse(
        items=[OfferResponse.model_validate(o) for o in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/offers/{offer_id}", response_model=OfferResponse)
async def get_offer(
    offer_id: str,
    service: Annotated[OfferService, Depends(get_offer_service)],
) -> OfferResponse:
    offer = await service.get_offer(offer_id)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return OfferResponse.model_validate(offer)


@router.post("/offers/manual", response_model=OfferResponse, status_code=201)
async def create_manual_offer(
    data: OfferCreateManual,
    service: Annotated[OfferService, Depends(get_offer_service)],
) -> OfferResponse:
    offer = await service.create_manual(data.model_dump())
    return OfferResponse.model_validate(offer)


@router.post("/offers/import-url", response_model=OfferResponse, status_code=201)
async def import_offer_url(
    data: OfferImportUrl,
    service: Annotated[OfferService, Depends(get_offer_service)],
) -> OfferResponse:
    try:
        offer = await service.import_from_url(data.url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OfferResponse.model_validate(offer)


@router.patch("/offers/{offer_id}", response_model=OfferResponse)
async def update_offer(
    offer_id: str,
    data: OfferUpdate,
    service: Annotated[OfferService, Depends(get_offer_service)],
) -> OfferResponse:
    offer = await service.update_offer(offer_id, **data.model_dump(exclude_unset=True))
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")
    return OfferResponse.model_validate(offer)


@router.delete("/offers/{offer_id}", status_code=204)
async def delete_offer(
    offer_id: str,
    service: Annotated[OfferService, Depends(get_offer_service)],
) -> None:
    if not await service.archive_offer(offer_id):
        raise HTTPException(status_code=404, detail="Offer not found")


@router.post("/scrape-runs", response_model=ScrapeRunResponse, status_code=201)
async def create_scrape_run(
    data: ScrapeRunCreate,
    service: Annotated[OfferService, Depends(get_offer_service)],
) -> ScrapeRunResponse:
    params = data.params
    sources = params.sources
    params_dict = params.model_dump(mode="json")
    run = await service.create_scrape_run(params_dict, sources)

    if data.save_config_as:
        await service.create_scrape_config(data.save_config_as, params_dict)

    enqueued = await enqueue_scrape_run(
        run.id, params_dict, [s.value for s in sources]
    )

    if not enqueued:
        scrape_params = ScrapeParams(
            keywords=params.keywords,
            location=params.location,
            greenhouse_slugs=params.greenhouse_slugs,
            lever_slugs=params.lever_slugs,
            since=params.since,
            max_results_per_source=params.max_results_per_source,
        )

        async def _run_in_background() -> None:
            from backend.db.session import async_session_factory

            async with async_session_factory() as session:
                bg_service = OfferService(session)
                await bg_service.run_scrape(run.id, scrape_params, sources)

        asyncio.create_task(_run_in_background())

    return ScrapeRunResponse.model_validate(run)


@router.get("/scrape-runs", response_model=list[ScrapeRunResponse])
async def list_scrape_runs(
    service: Annotated[OfferService, Depends(get_offer_service)],
    limit: int = Query(20, ge=1, le=100),
) -> list[ScrapeRunResponse]:
    runs = await service.list_scrape_runs(limit)
    return [ScrapeRunResponse.model_validate(r) for r in runs]


@router.get("/scrape-runs/{run_id}", response_model=ScrapeRunResponse)
async def get_scrape_run(
    run_id: str,
    service: Annotated[OfferService, Depends(get_offer_service)],
) -> ScrapeRunResponse:
    run = await service.get_scrape_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Scrape run not found")
    return ScrapeRunResponse.model_validate(run)


@router.get("/scrape-configs", response_model=list[ScrapeConfigResponse])
async def list_scrape_configs(
    service: Annotated[OfferService, Depends(get_offer_service)],
) -> list[ScrapeConfigResponse]:
    configs = await service.list_scrape_configs()
    return [ScrapeConfigResponse.model_validate(c) for c in configs]


@router.post("/scrape-configs", response_model=ScrapeConfigResponse, status_code=201)
async def create_scrape_config(
    data: ScrapeConfigCreate,
    service: Annotated[OfferService, Depends(get_offer_service)],
) -> ScrapeConfigResponse:
    cfg = await service.create_scrape_config(data.name, data.config.model_dump(mode="json"))
    return ScrapeConfigResponse.model_validate(cfg)


class OffersModule(BaseModule):
    name = "offers"

    def get_router(self) -> APIRouter:
        return router
