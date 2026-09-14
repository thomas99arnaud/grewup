import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from backend.db.base import Base


class ApplicationStatus(str, enum.Enum):
    DRAFT = "draft"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    HIRED = "hired"


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        Index("ix_applications_cv_signature", "cv_signature"),
        Index("ix_applications_offer_id", "offer_id"),
        Index("ix_applications_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    offer_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("offers.id", ondelete="SET NULL"),
        nullable=True,
    )
    company: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    job_title: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    offer_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="fr")
    cv_markdown: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cover_letter: Mapped[str] = mapped_column(Text, nullable=False, default="")
    fit_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    emphasized_experiences: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    omitted_experiences: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    cv_signature: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    reused_from_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("applications.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus),
        nullable=False,
        default=ApplicationStatus.DRAFT,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
