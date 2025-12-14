"""Schemas para reportes/alertas"""

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Schema genérico para respuestas paginadas"""

    items: list[T]
    total: int = Field(..., description="Total de items disponibles")
    page: int = Field(..., description="Página actual (empezando en 1)")
    page_size: int = Field(..., description="Tamaño de página")
    total_pages: int = Field(..., description="Total de páginas disponibles")


class AlertReportBase(BaseModel):
    """Schema base para reportes de alertas"""

    ai_explanation: str = Field(...,
                                description="Explicación de la IA sobre la alerta")
    ai_recommendation: str = Field(
        ..., description="Recomendación de la IA para solucionar el problema"
    )


class AlertReportCreate(AlertReportBase):
    """Schema para crear un nuevo reporte de alerta"""

    normalized_event_id: UUID = Field(...,
                                      description="ID del evento normalizado")


class AlertReportUpdate(BaseModel):
    """Schema para actualizar un reporte (cuando el usuario lo revisa)"""

    reviewer_name: str = Field(..., min_length=1, max_length=255)
    reviewer_explanation: str = Field(..., min_length=1)
    reviewer_solution: str = Field(..., min_length=1)


class AlertReportResponse(AlertReportBase):
    """Schema de respuesta completo del reporte"""

    id: UUID
    normalized_event_id: UUID
    status: str
    reviewer_name: str | None = None
    reviewer_explanation: str | None = None
    reviewer_solution: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertReportWithEvent(AlertReportResponse):
    """Schema de respuesta que incluye datos completos del evento normalizado"""

    # Todos los datos del evento normalizado
    # Core Payment Fields
    merchant_name: str
    provider: str
    country: str
    transactional_id: str | None

    # Status
    status_category: str
    failure_reason: str | None
    error_source: str | None
    http_status_code: int | None

    # Financial
    amount: float | None
    currency: str | None
    amount_usd_equivalent: float | None

    # Provider Details
    provider_transaction_id: str | None
    provider_status: str | None
    latency_ms: int | None

    # Normalization Metadata
    raw_data: dict | None = None
    normalization_method: str | None = None
    confidence_score: float | None
    event_metadata: dict | None = None

    # Timestamps del evento
    event_created_at: datetime
    normalized_at: datetime | None = None
    event_updated_at: datetime | None = None

    # Campos calculados para facilitar la visualización en tablas
    transaction_id: str = Field(...,
                                description="ID de transacción del proveedor o ID corto")
    title: str = Field(..., description="Título descriptivo del reporte")
    merchant: str = Field(..., description="Nombre del comerciante")
    severity: str = Field(..., description="Severidad: high, medium, low")
    transactions: int = Field(
        default=1, description="Número de transacciones relacionadas")
    date: datetime = Field(..., description="Fecha del evento")

    class Config:
        from_attributes = True

    class Config:
        from_attributes = True
