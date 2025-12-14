"""create users table

Revision ID: b1c2d3e4f5g6
Revises: 826026dec36c
Create Date: 2025-12-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5g6'
down_revision: Union[str, Sequence[str], None] = '826026dec36c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create roles enum type
    op.execute("CREATE TYPE roles AS ENUM ('ADMIN', 'CLIENT')")

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(
            length=255), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(
            length=100), nullable=False),
        sa.Column('password', sqlmodel.sql.sqltypes.AutoString(
            length=255), nullable=False),
        sa.Column('role', postgresql.ENUM('ADMIN', 'CLIENT',
                  name='roles', create_type=False), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.execute("DROP TYPE roles")
