"""create alert reports table

Revision ID: e1f2a3b4c5d6
Revises: 43461d7c7673, 8105441a6d10
Create Date: 2025-12-14 16:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, Sequence[str], None] = (
    '43461d7c7673', '8105441a6d10')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create alert_reports table
    op.create_table(
        'alert_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('normalized_event_id', postgresql.UUID(
            as_uuid=True), nullable=False),
        sa.Column('ai_explanation', sa.Text(), nullable=False),
        sa.Column('ai_recommendation', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50),
                  nullable=False, server_default='pending'),
        sa.Column('reviewer_name', sa.String(length=255), nullable=True),
        sa.Column('reviewer_explanation', sa.Text(), nullable=True),
        sa.Column('reviewer_solution', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['normalized_event_id'], [
                                'normalized_payment_events.id'], ),
    )

    # Create indexes
    op.create_index('idx_alert_reports_normalized_event_id',
                    'alert_reports', ['normalized_event_id'])
    op.create_index('idx_alert_reports_status', 'alert_reports', ['status'])
    op.create_index('idx_alert_reports_created_at',
                    'alert_reports', ['created_at'])
    op.create_index(op.f('ix_alert_reports_id'),
                    'alert_reports', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_alert_reports_id'), table_name='alert_reports')
    op.drop_index('idx_alert_reports_created_at', table_name='alert_reports')
    op.drop_index('idx_alert_reports_status', table_name='alert_reports')
    op.drop_index('idx_alert_reports_normalized_event_id',
                  table_name='alert_reports')
    op.drop_index('idx_normalized_event_id', table_name='alert_reports')
    op.drop_table('alert_reports')
