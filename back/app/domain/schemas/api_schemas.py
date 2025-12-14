"""Schemas para API REST - Request y Response DTOs"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.models.enums import FailureReason, NormalizationMethod, PaymentStatus


class EventIngestRequest(BaseModel):
    """Request body para POST /events"""

    raw_event: dict[str, Any] = Field(..., description="Evento de pago en cualquier formato")
    provider: str | None = Field(None, description="Hint del proveedor (opcional)")

    @field_validator("raw_event")
    @classmethod
    def validate_not_empty(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Valida que el evento crudo no esté vacío"""
        if not v:
            raise ValueError("raw_event cannot be empty")
        return v


class EventIngestResponse(BaseModel):
    """Response de ingesta exitosa"""

    id: UUID
    status: PaymentStatus
    normalization_method: NormalizationMethod
    confidence_score: float | None = None
    message: str = "Event ingested successfully"

    model_config = ConfigDict(from_attributes=True)


class EventDetailResponse(BaseModel):
    """Response detallada de un evento"""

    id: UUID
    merchant_name: str
    provider: str
    country: str
    status_category: PaymentStatus
    failure_reason: FailureReason | None
    # Multi-currency fields
    amount: Decimal | None
    currency: str | None
    amount_usd_equivalent: Decimal | None
    # Provider details
    provider_transaction_id: str | None
    normalization_method: NormalizationMethod
    confidence_score: float | None
    created_at: datetime
    normalized_at: datetime
    event_metadata: dict[str, Any] | None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "merchant_name": "Acme Corp",
                "provider": "stripe",
                "country": "US",
                "status_category": "approved",
                "failure_reason": None,
                "amount": 199.99,
                "currency": "USD",
                "amount_usd_equivalent": 199.99,
                "provider_transaction_id": "ch_3abc123",
                "normalization_method": "ai_based",
                "confidence_score": 0.95,
                "created_at": "2025-12-13T10:30:00Z",
                "normalized_at": "2025-12-13T10:30:01Z",
                "event_metadata": {"payment_method": "card"},
            }
        },
    )
