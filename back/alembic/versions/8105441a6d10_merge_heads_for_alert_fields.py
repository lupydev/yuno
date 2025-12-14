"""merge heads for alert fields

Revision ID: 8105441a6d10
Revises: 20f44bd4e8a3, d14f2ca8360e
Create Date: 2025-12-14 02:49:57.118760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8105441a6d10'
down_revision: Union[str, Sequence[str], None] = ('20f44bd4e8a3', 'd14f2ca8360e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
