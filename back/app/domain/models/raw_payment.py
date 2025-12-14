"""
Modelo para transacciones del Data Lake

Este modelo representa los datos crudos/heterogéneos que vienen del Data Lake
y que necesitan ser normalizados.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlmodel import JSON, Column, Field, SQLModel


class RawPaymentIngestion(SQLModel, table=True):
    """
    Modelo para transacciones sin procesar del Data Lake

    Esta tabla está en una base de datos externa (Data Lake) y contiene
    transacciones heterogéneas de múltiples proveedores de pago que
    necesitan ser normalizadas.
    """

    __tablename__ = "raw_payments_ingestion"

    # Primary Key
    id: UUID = Field(primary_key=True)

    # Payload JSONB que contiene toda la data heterogénea
    # Estructura esperada:
    # {
    #   "id": "uuid",
    #   "data": {...},  # ← Parte heterogénea que la IA debe normalizar
    #   "merchant": {"id": "uuid", "name": "...", "country": "..."},
    #   "transactional_id": "uuid"
    # }
    payload: dict[str, Any] = Field(sa_column=Column(JSON))

    # Flag de procesamiento
    is_processed: bool = Field(default=False, index=True)

    # Timestamps
    created_at: datetime = Field()
