"""(STABLE) Added Preferences column in userauth

Revision ID: ea82ec491487
Revises: e4560c87edfb
Create Date: 2025-06-14 14:19:38.064065

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea82ec491487'
down_revision: Union[str, None] = 'e4560c87edfb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    preference_enum = sa.Enum('RAW', 'CATEGORIZED_AND_ENRICHED', 'CATEGORIZED_AND_RAW', name='preferences')
    preference_enum.create(op.get_bind())

    op.add_column(
        'userauth',
        sa.Column('preference', preference_enum, nullable=False, server_default='CATEGORIZED_AND_ENRICHED')
    )


def downgrade() -> None:

    op.drop_column('userauth', 'preference')

    preference_enum = sa.Enum('RAW', 'CATEGORIZED_AND_ENRICHED', 'CATEGORIZED_AND_RAW', name='preferences')
    preference_enum.drop(op.get_bind())

