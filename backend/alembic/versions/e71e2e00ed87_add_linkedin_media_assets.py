"""add linkedin_media_assets field

Revision ID: e71e2e00ed87
Revises: 019a770eedc0
Create Date: 2024-03-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import TEXT, Column
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = 'e71e2e00ed87'
down_revision = '019a770eedc0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('contentpiece', sa.Column('linkedin_media_assets', JSONB, nullable=True))


def downgrade():
    op.drop_column('contentpiece', 'linkedin_media_assets')
