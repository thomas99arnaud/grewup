"""add profile languages and educations

Revision ID: 003
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "profile_languages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("profile_id", sa.String(36), sa.ForeignKey("candidate_profiles.id"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column(
            "level",
            sa.Enum("basic", "intermediate", "fluent", "bilingual", "native", name="languagelevel"),
            nullable=False,
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "educations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("profile_id", sa.String(36), sa.ForeignKey("candidate_profiles.id"), nullable=False),
        sa.Column("degree", sa.String(255), nullable=False),
        sa.Column("institution", sa.String(255), nullable=False),
        sa.Column("field_of_study", sa.String(255), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("educations")
    op.drop_table("profile_languages")
