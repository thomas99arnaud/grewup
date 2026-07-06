from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.module import module_registry
from backend.db.session import init_db
from backend.modules.offers.router import OffersModule

module_registry.register(OffersModule())


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    for module in module_registry.get_all():
        module.on_shutdown(app)


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in module_registry.get_all():
    app.include_router(module.get_router())
