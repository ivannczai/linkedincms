"""add_linkedin_media_assets_sheduled

Revision ID: a7704c000daf
Revises: e71e2e00ed87
Create Date: 2025-06-07 22:53:01.678702

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import TEXT, Column
from sqlalchemy.dialects.postgresql import JSONB



# revision identifiers, used by Alembic.
revision = 'a7704c000daf'
down_revision = 'e71e2e00ed87'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add media_assets column
    op.add_column('scheduledlinkedinpost', sa.Column('media_assets', JSONB, nullable=True))


def downgrade() -> None:
    # Remove media_assets column
    op.drop_column('scheduledlinkedinpost', 'media_assets') 