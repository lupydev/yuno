"""add missing fields to normalized_payment_events

Revision ID: 43461d7c7673
Revises: 8105441a6d10
Create Date: 2025-12-14 04:40:58.252797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '43461d7c7673'
down_revision: Union[str, Sequence[str], None] = '8105441a6d10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add transactional_id field to normalized_payment_events
    op.add_column('normalized_payment_events', sa.Column('transactional_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))

    # Update indexes for error_source
    op.drop_index('idx_error_source', table_name='normalized_payment_events', if_exists=True)
    op.create_index('idx_transactional_id', 'normalized_payment_events', ['transactional_id'], unique=False)
    op.create_index(op.f('ix_normalized_payment_events_error_source'), 'normalized_payment_events', ['error_source'], unique=False)
    op.create_index(op.f('ix_normalized_payment_events_transactional_id'), 'normalized_payment_events', ['transactional_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Rollback changes
    op.drop_index(op.f('ix_normalized_payment_events_transactional_id'), table_name='normalized_payment_events')
    op.drop_index(op.f('ix_normalized_payment_events_error_source'), table_name='normalized_payment_events')
    op.drop_index('idx_transactional_id', table_name='normalized_payment_events')
    op.create_index('idx_error_source', 'normalized_payment_events', ['error_source'], unique=False)
    op.drop_column('normalized_payment_events', 'transactional_id')
