import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class SkillLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LanguageLevel(str, enum.Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    FLUENT = "fluent"
    BILINGUAL = "bilingual"
    NATIVE = "native"


class CandidateProfile(Base):
    """Profil unique de l'utilisateur (singleton applicatif)."""

    __tablename__ = "candidate_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    headline: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    skills: Mapped[list["Skill"]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    languages: Mapped[list["ProfileLanguage"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    experiences: Mapped[list["Experience"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )
    educations: Mapped[list["Education"]] = relationship(
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


class ProfileLanguage(Base):
    __tablename__ = "profile_languages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_profiles.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[LanguageLevel] = mapped_column(
        Enum(LanguageLevel), nullable=False, default=LanguageLevel.INTERMEDIATE
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    profile: Mapped[CandidateProfile] = relationship(back_populates="languages")


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


class Education(Base):
    __tablename__ = "educations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidate_profiles.id"), nullable=False)
    degree: Mapped[str] = mapped_column(String(255), nullable=False)
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    field_of_study: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    profile: Mapped[CandidateProfile] = relationship(back_populates="educations")
