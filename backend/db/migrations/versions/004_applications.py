"""store generated applications

Revision ID: 004
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "applications",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("offer_id", sa.String(36), sa.ForeignKey("offers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("company", sa.String(512), nullable=False, server_default=""),
        sa.Column("job_title", sa.String(512), nullable=False, server_default=""),
        sa.Column("offer_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("language", sa.String(8), nullable=False, server_default="fr"),
        sa.Column("cv_markdown", sa.Text(), nullable=False, server_default=""),
        sa.Column("cover_letter", sa.Text(), nullable=False, server_default=""),
        sa.Column("fit_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("emphasized_experiences", sa.JSON(), nullable=False),
        sa.Column("omitted_experiences", sa.JSON(), nullable=False),
        sa.Column("cv_signature", sa.String(128), nullable=False, server_default=""),
        sa.Column(
            "reused_from_id",
            sa.String(36),
            sa.ForeignKey("applications.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.Enum("draft", "applied", "interview", "rejected", "hired", name="applicationstatus"),
            nullable=False,
            server_default="draft",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_applications_cv_signature", "applications", ["cv_signature"])
    op.create_index("ix_applications_offer_id", "applications", ["offer_id"])
    op.create_index("ix_applications_status", "applications", ["status"])


def downgrade() -> None:
    op.drop_index("ix_applications_status", table_name="applications")
    op.drop_index("ix_applications_offer_id", table_name="applications")
    op.drop_index("ix_applications_cv_signature", table_name="applications")
    op.drop_table("applications")
    op.execute("DROP TYPE IF EXISTS applicationstatus")
