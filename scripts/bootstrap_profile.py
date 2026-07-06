"""One-shot script to scaffold the profile module (UTF-8 safe on Windows)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES: dict[str, str] = {}

FILES["backend/modules/profile/models.py"] = '''import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from backend.db.base import Base


class SkillLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    headline: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    languages: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    skills: Mapped[list["Skill"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    experiences: Mapped[list["Experience"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_profiles.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    level: Mapped[SkillLevel] = mapped_column(Enum(SkillLevel), nullable=False, default=SkillLevel.INTERMEDIATE)
    years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    profile: Mapped[CandidateProfile] = relationship(back_populates="skills")


class Experience(Base):
    __tablename__ = "experiences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_profiles.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    profile: Mapped[CandidateProfile] = relationship(back_populates="experiences")
'''

FILES["backend/modules/profile/schemas.py"] = '''from datetime import date, datetime

from pydantic import BaseModel, Field

from backend.modules.profile.models import SkillLevel


class ProfileBase(BaseModel):
    full_name: str = ""
    headline: str = ""
    summary: str = ""
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin_url: str | None = None
    languages: list[str] = Field(default_factory=list)


class ProfileUpdate(ProfileBase):
    pass


class SkillBase(BaseModel):
    name: str
    category: str | None = None
    level: SkillLevel = SkillLevel.INTERMEDIATE
    years: int | None = None
    description: str | None = None
    sort_order: int = 0


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    level: SkillLevel | None = None
    years: int | None = None
    description: str | None = None
    sort_order: int | None = None


class SkillResponse(SkillBase):
    id: str
    profile_id: str

    model_config = {"from_attributes": True}


class ExperienceBase(BaseModel):
    title: str
    company: str
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    description: str = ""
    sort_order: int = 0


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    description: str | None = None
    sort_order: int | None = None


class ExperienceResponse(ExperienceBase):
    id: str
    profile_id: str

    model_config = {"from_attributes": True}


class ProfileResponse(ProfileBase):
    id: str
    skills: list[SkillResponse] = Field(default_factory=list)
    experiences: list[ExperienceResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
'''

FILES["backend/modules/profile/service.py"] = '''from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.events import event_bus
from backend.modules.profile.models import CandidateProfile, Experience, Skill


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _get_or_create_profile(self) -> CandidateProfile:
        result = await self.session.execute(
            select(CandidateProfile)
            .options(selectinload(CandidateProfile.skills), selectinload(CandidateProfile.experiences))
            .limit(1)
        )
        profile = result.scalar_one_or_none()
        if profile:
            return profile

        profile = CandidateProfile()
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def get_profile(self) -> CandidateProfile:
        return await self._get_or_create_profile()

    async def update_profile(self, data: dict) -> CandidateProfile:
        profile = await self._get_or_create_profile()
        for key, value in data.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=profile.id)
        return profile

    async def create_skill(self, data: dict) -> Skill:
        profile = await self._get_or_create_profile()
        skill = Skill(profile_id=profile.id, **data)
        self.session.add(skill)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=profile.id)
        return skill

    async def update_skill(self, skill_id: str, data: dict) -> Skill | None:
        skill = await self.session.get(Skill, skill_id)
        if not skill:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(skill, key, value)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=skill.profile_id)
        return skill

    async def delete_skill(self, skill_id: str) -> bool:
        skill = await self.session.get(Skill, skill_id)
        if not skill:
            return False
        profile_id = skill.profile_id
        await self.session.delete(skill)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=profile_id)
        return True

    async def create_experience(self, data: dict) -> Experience:
        profile = await self._get_or_create_profile()
        experience = Experience(profile_id=profile.id, **data)
        self.session.add(experience)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=profile.id)
        return experience

    async def update_experience(self, experience_id: str, data: dict) -> Experience | None:
        experience = await self.session.get(Experience, experience_id)
        if not experience:
            return None
        for key, value in data.items():
            if value is not None:
                setattr(experience, key, value)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=experience.profile_id)
        return experience

    async def delete_experience(self, experience_id: str) -> bool:
        experience = await self.session.get(Experience, experience_id)
        if not experience:
            return False
        profile_id = experience.profile_id
        await self.session.delete(experience)
        await self.session.flush()
        await event_bus.emit("profile.updated", profile_id=profile_id)
        return True
'''

FILES["backend/modules/profile/router.py"] = '''from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.module import BaseModule
from backend.db.session import get_session
from backend.modules.profile.schemas import (
    ExperienceCreate,
    ExperienceResponse,
    ExperienceUpdate,
    ProfileResponse,
    ProfileUpdate,
    SkillCreate,
    SkillResponse,
    SkillUpdate,
)
from backend.modules.profile.service import ProfileService

router = APIRouter(prefix="/api", tags=["profile"])


def get_profile_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProfileService:
    return ProfileService(session)


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    profile = await service.get_profile()
    return ProfileResponse.model_validate(profile)


@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ProfileResponse:
    profile = await service.update_profile(data.model_dump())
    return ProfileResponse.model_validate(profile)


@router.post("/profile/skills", response_model=SkillResponse, status_code=201)
async def create_skill(
    data: SkillCreate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> SkillResponse:
    skill = await service.create_skill(data.model_dump())
    return SkillResponse.model_validate(skill)


@router.patch("/profile/skills/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    data: SkillUpdate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> SkillResponse:
    skill = await service.update_skill(skill_id, data.model_dump(exclude_unset=True))
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return SkillResponse.model_validate(skill)


@router.delete("/profile/skills/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> None:
    if not await service.delete_skill(skill_id):
        raise HTTPException(status_code=404, detail="Skill not found")


@router.post("/profile/experiences", response_model=ExperienceResponse, status_code=201)
async def create_experience(
    data: ExperienceCreate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ExperienceResponse:
    experience = await service.create_experience(data.model_dump())
    return ExperienceResponse.model_validate(experience)


@router.patch("/profile/experiences/{experience_id}", response_model=ExperienceResponse)
async def update_experience(
    experience_id: str,
    data: ExperienceUpdate,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> ExperienceResponse:
    experience = await service.update_experience(experience_id, data.model_dump(exclude_unset=True))
    if not experience:
        raise HTTPException(status_code=404, detail="Experience not found")
    return ExperienceResponse.model_validate(experience)


@router.delete("/profile/experiences/{experience_id}", status_code=204)
async def delete_experience(
    experience_id: str,
    service: Annotated[ProfileService, Depends(get_profile_service)],
) -> None:
    if not await service.delete_experience(experience_id):
        raise HTTPException(status_code=404, detail="Experience not found")


class ProfileModule(BaseModule):
    name = "profile"

    def get_router(self) -> APIRouter:
        return router
'''

FILES["backend/db/migrations/versions/002_profile.py"] = '''"""add profile tables

Revision ID: 002
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("headline", sa.String(512), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("linkedin_url", sa.String(512), nullable=True),
        sa.Column("languages", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "skills",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("profile_id", sa.String(36), sa.ForeignKey("candidate_profiles.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("level", sa.Enum("beginner", "intermediate", "advanced", "expert", name="skilllevel"), nullable=False),
        sa.Column("years", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "experiences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("profile_id", sa.String(36), sa.ForeignKey("candidate_profiles.id"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("experiences")
    op.drop_table("skills")
    op.drop_table("candidate_profiles")
'''

FILES["backend/main.py"] = '''from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.module import module_registry
from backend.db.session import init_db
from backend.modules.offers.router import OffersModule
from backend.modules.profile.router import ProfileModule

module_registry.register(OffersModule())
module_registry.register(ProfileModule())


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
'''

# env.py patch content
env_py = (ROOT / "backend/db/migrations/env.py").read_bytes()
if b"\x00" in env_py:
    env_text = env_py.decode("utf-16-le")
else:
    env_text = env_py.decode("utf-8")

if "profile.models" not in env_text:
    env_text = env_text.replace(
        "from backend.modules.offers.models import Offer, ScrapeConfig, ScrapeRun  # noqa: F401",
        "from backend.modules.offers.models import Offer, ScrapeConfig, ScrapeRun  # noqa: F401\n"
        "from backend.modules.profile.models import CandidateProfile, Experience, Skill  # noqa: F401",
    )
FILES["backend/db/migrations/env.py"] = env_text

for rel, content in FILES.items():
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print("wrote", rel)

print("done")
