"""(STABLE) edited notion block model

Revision ID: 52e8553a9cce
Revises: 37407c620843
Create Date: 2025-06-18 14:01:40.367140

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '52e8553a9cce'
down_revision: Union[str, None] = '37407c620843'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the existing table and recreate with new schema
    op.drop_table('notion_blocks')
    
    # Create the table with the new schema
    op.create_table('notion_blocks',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('notion_block_id', sa.String(), nullable=False),
        sa.Column('notion_page_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('block_type', sa.String(), nullable=True),
        sa.Column('plain_text_content', sa.Text(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('qdrant_point_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['notion_page_id'], ['notion_pages.notion_page_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['userauth.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('notion_block_id'),
        sa.UniqueConstraint('qdrant_point_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the table and recreate with old schema
    op.drop_table('notion_blocks')
    
    # Create the table with the old schema (UUID id)
    op.create_table('notion_blocks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('notion_block_id', sa.String(), nullable=False),
        sa.Column('notion_page_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('block_type', sa.String(), nullable=True),
        sa.Column('plain_text_content', sa.Text(), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('qdrant_point_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['notion_page_id'], ['notion_pages.notion_page_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['userauth.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('notion_block_id'),
        sa.UniqueConstraint('qdrant_point_id')
    )
