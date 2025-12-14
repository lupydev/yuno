"""Schemas relacionados con normalización de eventos de pago"""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.domain.models.enums import FailureReason, PaymentStatus


class NormalizedPaymentSchema(BaseModel):
    """
    Schema para normalización de eventos de pago (sin campos de auditoría)

    Este schema es usado por los normalizadores (AI y Rule-based) para
    retornar datos normalizados sin incluir campos de auditoría como
    id, created_at, etc.
    """

    # Core Payment Fields
    merchant_name: str = Field(..., min_length=1, max_length=255)
    provider: str = Field(..., min_length=1, max_length=100)
    country: str = Field(..., min_length=2, max_length=2)

    # Status
    status_category: PaymentStatus
    failure_reason: FailureReason | None = None

    # Financial (dual storage: original + USD equivalent)
    amount: Decimal = Field(..., gt=0, description="Transaction amount in original currency")
    currency: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 currency code (USD, EUR, MXN, etc.)"
    )
    amount_usd_equivalent: Decimal | None = Field(
        default=None, gt=0, description="Amount in USD for analytics (calculated at normalization)"
    )

    # Provider Details
    provider_transaction_id: str | None = None
    provider_status: str | None = None
    latency_ms: int | None = Field(default=None, ge=0)

    # Additional Metadata
    event_metadata: dict[str, Any] | None = None

    # Validaciones de Negocio (Best Practice: validaciones en schemas, no en modelos)
    @field_validator("country")
    @classmethod
    def validate_country_code(cls, v: str) -> str:
        """Valida que el código de país sea ISO 3166-1 alpha-2"""
        if len(v) != 2:
            raise ValueError("Country code must be 2 characters (ISO 3166-1 alpha-2)")
        return v.upper()

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        """Valida que el monto sea positivo"""
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        """Valida que el código de moneda sea ISO 4217 (3 caracteres)"""
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters (ISO 4217)")
        return v.upper()

    @field_validator("provider", "merchant_name")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Valida que los campos de texto no estén vacíos (strip whitespace)"""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("latency_ms")
    @classmethod
    def validate_latency(cls, v: int | None) -> int | None:
        """Valida que latency sea razonable (< 5 minutos)"""
        if v is not None and v > 300000:  # 5 minutos en ms
            raise ValueError("Latency seems unrealistic (> 5 minutes)")
        return v


class RawEventInput(BaseModel):
    """
    Schema para validación de entrada de eventos crudos

    Valida que el evento crudo tenga la estructura mínima requerida
    antes de ser procesado por los normalizadores.
    """

    raw_event: dict[str, Any] = Field(..., min_length=1)
    provider: str | None = Field(
        default=None, description="Hint del proveedor (opcional, ayuda a la normalización)"
    )
    source: str | None = Field(
        default=None, description="Fuente del evento (api, webhook, data_lake, etc.)"
    )

    @field_validator("raw_event")
    @classmethod
    def validate_not_empty(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Valida que el evento crudo no esté vacío"""
        if not v:
            raise ValueError("raw_event cannot be empty")
        return v
