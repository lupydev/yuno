"""add teams and update users with roles

Revision ID: a1b2c3d4e5f6
Revises: b1c2d3e4f5g6
Create Date: 2025-12-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'b1c2d3e4f5g6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create teams table
    op.create_table(
        'teams',
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(
            length=100), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('name')
    )

    # Add team_id column to users table
    op.add_column('users', sa.Column('team_id', sqlmodel.sql.sqltypes.AutoString(
        length=100), nullable=True))
    op.create_foreign_key('fk_users_team_id', 'users',
                          'teams', ['team_id'], ['name'])

    # Update role enum to include DEVELOPER
    # Note: PostgreSQL requires explicit enum type modification
    op.execute("ALTER TYPE roles ADD VALUE IF NOT EXISTS 'DEVELOPER'")


def downgrade() -> None:
    """Downgrade schema."""
    # Remove foreign key and team_id column from users
    op.drop_constraint('fk_users_team_id', 'users', type_='foreignkey')
    op.drop_column('users', 'team_id')

    # Drop teams table
    op.drop_table('teams')

    # Note: Cannot remove enum value from PostgreSQL enum type
    # This is a PostgreSQL limitation - enum values cannot be removed
