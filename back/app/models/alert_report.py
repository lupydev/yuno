"""Modelo para reportes/alertas de eventos de pago"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import sqlalchemy
from sqlmodel import Field, SQLModel


def get_utc_now() -> datetime:
    """Retorna la fecha y hora actual en UTC"""
    return datetime.now(UTC)


class AlertReport(SQLModel, table=True):
    """
    Modelo de reportes/alertas generados a partir de eventos de pago normalizados

    Cada reporte contiene:
    - Referencia al evento normalizado
    - Análisis generado por IA
    - Estado de revisión
    - Información del revisor
    """

    __tablename__ = "alert_reports"

    # Índices para búsquedas eficientes
    __table_args__ = (
        sqlalchemy.Index("idx_normalized_event_id", "normalized_event_id"),
        sqlalchemy.Index("idx_status", "status"),
        sqlalchemy.Index("idx_created_at", "created_at"),
    )

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)

    # Relación con el evento normalizado
    normalized_event_id: UUID = Field(
        foreign_key="normalized_payment_events.id",
        description="ID del evento de pago normalizado",
    )

    # Análisis generado por IA
    ai_explanation: str = Field(
        description="Explicación generada por IA sobre por qué se generó la alerta"
    )
    ai_recommendation: str = Field(
        description="Recomendación generada por IA para solucionar el problema"
    )

    # Estado del reporte
    status: str = Field(
        default="pending",
        max_length=50,
        description="Estado del reporte: pending o reviewed",
    )

    # Información del revisor (vacío inicialmente)
    reviewer_name: str | None = Field(
        default=None, max_length=255, description="Nombre de quien atendió el reporte"
    )
    reviewer_explanation: str | None = Field(
        default=None, description="Explicación del usuario sobre el problema"
    )
    reviewer_solution: str | None = Field(
        default=None, description="Solución aplicada por el usuario"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=get_utc_now,
        sa_type=sqlalchemy.DateTime(timezone=True),
        sa_column_kwargs={"server_default": sqlalchemy.func.now()},
        index=True,
        description="Fecha de creación del reporte",
    )
    reviewed_at: datetime | None = Field(
        default=None,
        sa_type=sqlalchemy.DateTime(timezone=True),
        description="Fecha de revisión del reporte",
    )
    updated_at: datetime = Field(
        default_factory=get_utc_now,
        sa_type=sqlalchemy.DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": sqlalchemy.func.now(),
            "server_default": sqlalchemy.func.now(),
        },
        description="Última actualización",
    )
