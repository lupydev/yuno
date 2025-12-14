"""Modelo principal de eventos de pago normalizados"""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy
from sqlmodel import JSON, Column, Field, SQLModel

from app.domain.models.enums import ErrorSource, FailureReason, NormalizationMethod, PaymentStatus


def get_utc_now() -> datetime:
    """Retorna la fecha y hora actual en UTC"""
    return datetime.now(UTC)


class NormalizedPaymentEvent(SQLModel, table=True):
    """
    Modelo principal de eventos de pago normalizados

    Almacena todos los eventos de pago en un formato estandarizado,
    independientemente del proveedor de pagos original.

    NOTA: Este modelo es PURO - solo define estructura y constraints de BD.
    Las validaciones de negocio están en los schemas (normalization_schemas.py).
    """

    __tablename__ = "normalized_payment_events"  # type: ignore[assignment]

    # Índices compuestos para queries comunes (Best Practice)
    __table_args__ = (
        sqlalchemy.Index("idx_created_at", "created_at"),
        sqlalchemy.Index("idx_provider_status", "provider", "status_category"),
        sqlalchemy.Index("idx_merchant_country", "merchant_name", "country"),
        sqlalchemy.Index(
            "idx_analytics",
            "provider",
            "status_category",
            "created_at",
        ),
        sqlalchemy.Index("idx_transactional_id", "transactional_id"),
        sqlalchemy.Index(
            "idx_error_analysis",
            "error_source",
            "failure_reason",
            "status_category",
        ),
    )

    # Primary Key
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)

    # Core Payment Fields
    merchant_name: str = Field(max_length=255, index=True)
    provider: str = Field(
        max_length=100, index=True, description="Payment provider (stripe, adyen, etc.)"
    )
    country: str = Field(max_length=2, description="ISO 3166-1 alpha-2 country code")
    transactional_id: str | None = Field(
        default=None,
        max_length=255,
        index=True,
        description="Merchant-Provider connection ID from Data Lake (multiple events can share same transactional_id)",
    )

    # Status
    status_category: PaymentStatus = Field(index=True, description="Normalized payment status")
    failure_reason: FailureReason | None = Field(
        default=None, description="Specific failure reason if applicable"
    )
    error_source: ErrorSource | None = Field(
        default=None,
        index=True,
        description="Who/what caused the error (provider, merchant, customer, network, system)",
    )
    http_status_code: int | None = Field(
        default=None,
        ge=100,
        le=599,
        description="HTTP status code from provider response (for coherence validation)",
    )

    # Financial (dual storage: original + USD equivalent for analytics)
    # OPTIONAL: Error events may not contain amount/currency information
    amount: Decimal | None = Field(
        default=None,
        max_digits=15,
        decimal_places=2,
        description="Transaction amount in original currency (optional - may be null for error events)",
    )
    currency: str | None = Field(
        default=None,
        max_length=3,
        description="ISO 4217 currency code (USD, EUR, MXN, etc.) - optional for error events",
    )
    amount_usd_equivalent: Decimal | None = Field(
        default=None,
        max_digits=15,
        decimal_places=2,
        description="Amount converted to USD for analytics (using exchange rate at normalization time)",
    )

    # Provider Details
    provider_transaction_id: str | None = Field(
        default=None,
        max_length=255,
        index=True,
        description="Original transaction ID from provider",
    )
    provider_status: str | None = Field(
        default=None, max_length=100, description="Original status from provider"
    )
    latency_ms: int | None = Field(
        default=None, ge=0, description="Transaction latency in milliseconds"
    )

    # Normalization Metadata
    raw_data: dict[str, Any] = Field(sa_column=Column(JSON), description="Original raw event data")
    normalization_method: NormalizationMethod = Field(
        description="Method used to normalize this event"
    )
    confidence_score: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score of normalization (0-1)",
    )

    # Additional Metadata
    event_metadata: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON), description="Additional custom metadata"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=get_utc_now,
        sa_type=sqlalchemy.DateTime(timezone=True),
        sa_column_kwargs={"server_default": sqlalchemy.func.now()},
        index=True,
        description="When event was created in our system",
    )
    normalized_at: datetime = Field(
        default_factory=get_utc_now,
        sa_type=sqlalchemy.DateTime(timezone=True),
        sa_column_kwargs={"server_default": sqlalchemy.func.now()},
        description="When event was normalized",
    )
    updated_at: datetime = Field(
        default_factory=get_utc_now,
        sa_type=sqlalchemy.DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": sqlalchemy.func.now(),
            "server_default": sqlalchemy.func.now(),
        },
        description="Last update timestamp",
    )
