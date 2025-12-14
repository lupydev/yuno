"""add_server_default_to_teams_created

Revision ID: d14f2ca8360e
Revises: c1d2e3f4g5h6
Create Date: 2025-12-14 01:48:34.852725

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd14f2ca8360e'
down_revision: Union[str, Sequence[str], None] = 'c1d2e3f4g5h6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add server default to created column
    op.execute("ALTER TABLE teams ALTER COLUMN created SET DEFAULT NOW()")
    # Update existing rows with NULL created values
    op.execute("UPDATE teams SET created = NOW() WHERE created IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove server default from created column
    op.execute("ALTER TABLE teams ALTER COLUMN created DROP DEFAULT")
