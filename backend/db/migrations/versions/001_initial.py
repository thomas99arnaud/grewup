"""initial

Revision ID: 001
Revises:
Create Date: 2026-07-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "offers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.Enum("wttj", "indeed", "greenhouse", "lever", "manual", name="offersource"), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("company", sa.String(512), nullable=False),
        sa.Column("location", sa.String(512), nullable=True),
        sa.Column("remote_type", sa.Enum("onsite", "hybrid", "remote", name="remotetype"), nullable=True),
        sa.Column("contract_type", sa.String(128), nullable=True),
        sa.Column("description_raw", sa.Text(), nullable=False),
        sa.Column("description_parsed", sa.JSON(), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("salary_currency", sa.String(8), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", sa.Enum("new", "reviewed", "shortlisted", "archived", name="offerstatus"), nullable=False),
        sa.Column("compatibility_score", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("url"),
    )
    op.create_index("ix_offers_url", "offers", ["url"])
    op.create_index("ix_offers_source_external_id", "offers", ["source", "external_id"])

    op.create_table(
        "scrape_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("status", sa.Enum("pending", "running", "done", "failed", name="scraperunstatus"), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("offers_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("offers_new", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("offers_duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "scrape_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("scrape_configs")
    op.drop_table("scrape_runs")
    op.drop_index("ix_offers_source_external_id", table_name="offers")
    op.drop_index("ix_offers_url", table_name="offers")
    op.drop_table("offers")
