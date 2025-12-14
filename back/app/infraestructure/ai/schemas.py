"""
Schemas intermedios para AI Normalization

Estos schemas son usados específicamente por el AI normalizer
para recibir structured output de OpenAI.

NOTA: Los campos coinciden lo más posible con el modelo de BD
para minimizar mapeo manual.
"""

from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.models.enums import FailureReason, PaymentStatus


class AIPaymentNormalizationOutput(BaseModel):
    """
    Schema para structured output de OpenAI

    Este schema recibe la respuesta de la IA. Los campos se mapean
    directamente a NormalizedPaymentEvent con transformaciones mínimas.

    Transformaciones necesarias:
    - merchant_name (puede venir como null si no está en raw event)
    - provider → lowercased, normalizando
    - country → puede ser null
    - amount_usd y currency → se calculan después (conversión)
    - provider_status → extraído del raw event
    """

    # Core fields que retorna la IA
    merchant_name: str | None = Field(default="unknown_merchant", description="Merchant name or ID")
    provider: str = Field(..., description="Payment provider (stripe, adyen, etc.)")
    provider_transaction_id: str | None = Field(
        default=None, description="Original transaction ID from provider"
    )
    provider_status: str | None = Field(
        default=None, description="Original status code from provider"
    )

    # Location
    country: str | None = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code (e.g. US, GB, MX)",
    )

    # Status
    status_category: PaymentStatus = Field(..., description="Normalized payment status")
    failure_reason: FailureReason | None = Field(
        default=None,
        description="Specific failure reason (only if status is FAILED)",
    )

    # Financial - AI retorna amount + currency, luego convertimos a USD
    amount: Decimal = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(
        ..., min_length=3, max_length=3, description="ISO 4217 currency code (USD, EUR, etc.)"
    )

    # Latency (opcional)
    latency_ms: int | None = Field(
        default=None, ge=0, description="Payment latency in milliseconds"
    )
