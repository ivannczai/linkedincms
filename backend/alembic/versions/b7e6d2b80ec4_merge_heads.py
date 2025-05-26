"""Merge heads

Revision ID: b7e6d2b80ec4
Revises: 1a2b3c4d5e6f, create_content_linkedin_posts_table
Create Date: 2025-05-26 18:53:56.375512

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'b7e6d2b80ec4'
down_revision = ('1a2b3c4d5e6f', 'create_content_linkedin_posts_table')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
