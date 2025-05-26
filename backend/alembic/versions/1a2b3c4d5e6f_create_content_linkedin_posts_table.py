"""create content linkedin posts table

Revision ID: create_content_linkedin_posts_table
Revises: c3f6b5d13cdf
Create Date: 2024-03-26 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'create_content_linkedin_posts_table'
down_revision = 'c3f6b5d13cdf'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'contentlinkedinpost',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('linkedin_post_id', sa.String(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['content_id'], ['contentpiece.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contentlinkedinpost_id'), 'contentlinkedinpost', ['id'], unique=False)
    op.create_index(op.f('ix_contentlinkedinpost_user_id'), 'contentlinkedinpost', ['user_id'], unique=False)
    op.create_index(op.f('ix_contentlinkedinpost_content_id'), 'contentlinkedinpost', ['content_id'], unique=False)
    op.create_index(op.f('ix_contentlinkedinpost_status'), 'contentlinkedinpost', ['status'], unique=False)
    op.create_index(op.f('ix_contentlinkedinpost_scheduled_at'), 'contentlinkedinpost', ['scheduled_at'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_contentlinkedinpost_scheduled_at'), table_name='contentlinkedinpost')
    op.drop_index(op.f('ix_contentlinkedinpost_status'), table_name='contentlinkedinpost')
    op.drop_index(op.f('ix_contentlinkedinpost_content_id'), table_name='contentlinkedinpost')
    op.drop_index(op.f('ix_contentlinkedinpost_user_id'), table_name='contentlinkedinpost')
    op.drop_index(op.f('ix_contentlinkedinpost_id'), table_name='contentlinkedinpost')
    op.drop_table('contentlinkedinpost') 