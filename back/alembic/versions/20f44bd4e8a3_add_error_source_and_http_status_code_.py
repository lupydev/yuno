"""add error_source and http_status_code for alerts

Revision ID: 20f44bd4e8a3
Revises: 080e138beb3e
Create Date: 2025-12-14 02:49:04.357724

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20f44bd4e8a3'
down_revision: Union[str, Sequence[str], None] = '080e138beb3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add error_source and http_status_code for intelligent alerts."""

    # 1. Crear ENUM ErrorSource (solo si no existe)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE errorsource AS ENUM (
                'provider', 'merchant', 'customer', 'system', 'network', 'unknown'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 2. Agregar columna error_source (nullable para datos existentes)
    op.add_column('normalized_payment_events',
        sa.Column('error_source', sa.Enum('provider', 'merchant', 'customer', 'system', 'network', 'unknown', name='errorsource'), nullable=True)
    )

    # 3. Agregar columna http_status_code (nullable)
    op.add_column('normalized_payment_events',
        sa.Column('http_status_code', sa.Integer(), nullable=True)
    )

    # 4. Hacer amount y currency nullable (para eventos de error sin info financiera)
    op.alter_column('normalized_payment_events', 'amount',
                    existing_type=sa.NUMERIC(precision=15, scale=2),
                    nullable=True)

    op.alter_column('normalized_payment_events', 'currency',
                    existing_type=sa.String(length=3),
                    nullable=True)

    # 5. Crear índices para queries de alertas
    op.create_index('idx_error_source', 'normalized_payment_events', ['error_source'])
    op.create_index('idx_error_analysis', 'normalized_payment_events',
                   ['error_source', 'failure_reason', 'status_category'])


def downgrade() -> None:
    """Downgrade schema - Remove alert fields."""

    # Remover índices
    op.drop_index('idx_error_analysis', table_name='normalized_payment_events')
    op.drop_index('idx_error_source', table_name='normalized_payment_events')

    # Remover columnas
    op.drop_column('normalized_payment_events', 'http_status_code')
    op.drop_column('normalized_payment_events', 'error_source')

    # Volver amount y currency a NOT NULL (si es necesario revertir)
    # NOTA: Esto puede fallar si hay NULLs en los datos
    # op.alter_column('normalized_payment_events', 'amount', nullable=False)
    # op.alter_column('normalized_payment_events', 'currency', nullable=False)

    # NO eliminar el ENUM type porque puede estar en uso en otras tablas
