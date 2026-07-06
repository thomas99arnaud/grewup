from pathlib import Path

SESSION = """from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.config import settings
from backend.db.base import Base

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
"""

INIT = """from backend.db.base import Base
from backend.db.session import async_session_factory, engine, get_session, init_db

__all__ = ["Base", "engine", "async_session_factory", "get_session", "init_db"]
"""

for path, content in [
    (Path("backend/db/session.py"), SESSION),
    (Path("backend/db/__init__.py"), INIT),
]:
    path.write_text(content, encoding="utf-8", newline="\n")
    print("wrote", path)
