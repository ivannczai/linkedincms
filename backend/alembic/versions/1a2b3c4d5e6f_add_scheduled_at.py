"""add scheduled_at column

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2024-05-26 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1a2b3c4d5e6f'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('contentpiece', sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('contentpiece', 'scheduled_at') 