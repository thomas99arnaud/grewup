"""add profile tables

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
