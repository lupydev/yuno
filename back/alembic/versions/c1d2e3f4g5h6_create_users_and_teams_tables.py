"""create users and teams tables

Revision ID: c1d2e3f4g5h6
Revises: 041d47bcb649
Create Date: 2025-12-14 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4g5h6'
down_revision: Union[str, Sequence[str], None] = '041d47bcb649'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create roles enum if not exists
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE roles AS ENUM ('ADMIN', 'DEVELOPER', 'CLIENT');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Create teams table if not exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            name VARCHAR(100) NOT NULL,
            created TIMESTAMP NOT NULL,
            PRIMARY KEY (name)
        )
    """)

    # Create users table if not exists
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID NOT NULL,
            email VARCHAR(255) NOT NULL,
            name VARCHAR(100) NOT NULL,
            password VARCHAR(255) NOT NULL,
            role roles NOT NULL,
            team_id VARCHAR(100),
            is_active BOOLEAN NOT NULL,
            created TIMESTAMP NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY(team_id) REFERENCES teams (name)
        )
    """)

    # Create indexes if not exist
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_users_email', table_name='users', if_exists=True)
    op.drop_table('users', if_exists=True)
    op.drop_table('teams', if_exists=True)
    op.execute("DROP TYPE IF EXISTS roles")
