"""merge multiple heads

Revision ID: 041d47bcb649
Revises: 080e138beb3e, a1b2c3d4e5f6
Create Date: 2025-12-14 01:17:15.822833

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '041d47bcb649'
down_revision: Union[str, Sequence[str], None] = ('080e138beb3e', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
