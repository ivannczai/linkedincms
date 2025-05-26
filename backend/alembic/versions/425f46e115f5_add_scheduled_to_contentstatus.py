"""Add SCHEDULED to contentstatus enum

Revision ID: 425f46e115f5
Revises: 93b1a9ea9f1f
Create Date: 2025-05-24 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '425f46e115f5'
down_revision = '93b1a9ea9f1f'
branch_labels = None
depends_on = None


def upgrade():
    # Create a new enum type with the additional value
    op.execute("ALTER TYPE contentstatus ADD VALUE IF NOT EXISTS 'SCHEDULED'")


def downgrade():
    # Note: PostgreSQL does not support removing values from enum types
    # We can only create a new type without the value and replace the old one
    # This is complex and potentially dangerous, so we'll leave it as is
    pass
