"""added is_loggedin field

Revision ID: 3c007b51ea92
Revises: c09d8aa547a1
Create Date: 2025-06-13 00:04:58.931184

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3c007b51ea92'
down_revision: Union[str, None] = 'c09d8aa547a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('userauth', sa.Column('is_logged_in', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('userauth', 'is_logged_in')
    # ### end Alembic commands ###
