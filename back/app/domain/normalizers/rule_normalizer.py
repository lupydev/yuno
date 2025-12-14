"""
Rule-Based Payment Normalizer

Normaliza eventos de payment providers conocidos usando reglas predefinidas.

Design:
- Sin llamadas externas (rápido y determinístico)
- Mapeos específicos por provider (Stripe, Adyen, MercadoPago)
- Confidence score moderado (0.7-0.8)
- Fallback a AI si provider no reconocido

Use Cases:
- Providers con estructura estable y bien documentada
- Cuando queremos evitar costos de IA
- Para reducir latencia en casos comunes
- Como validación de AI (comparar resultados)

Architecture:
- Factory pattern para seleccionar mapper por provider
- Cada provider tiene su propio mapper
- Fácil extender con nuevos providers
"""

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from app.domain.exceptions import NormalizationException
from app.domain.interfaces.normalizer import INormalizer
from app.domain.models.enums import (
    FailureReason,
    NormalizationMethod,
    PaymentStatus,
)
from app.domain.models.payment_event import NormalizedPaymentEvent
from app.domain.utils.currency_converter import convert_to_usd

logger = logging.getLogger(__name__)


# ============================================================================
# PROVIDER MAPPERS
# ============================================================================


class BaseProviderMapper(ABC):
    """
    Base class para mappers de providers específicos

    Cada provider implementa su propia lógica de mapeo.
    """

    provider_name: str
    confidence_score: float = 0.75

    @abstractmethod
    def can_handle(self, raw_event: dict[str, Any]) -> bool:
        """Verifica si este mapper puede procesar el evento"""
        pass

    @abstractmethod
    def map_status(self, raw_event: dict[str, Any]) -> PaymentStatus:
        """Mapea status del provider a PaymentStatus estándar"""
        pass

    @abstractmethod
    def map_failure_reason(self, raw_event: dict[str, Any]) -> FailureReason | None:
        """Mapea error del provider a FailureReason estándar"""
        pass

    @abstractmethod
    def extract_fields(self, raw_event: dict[str, Any]) -> dict[str, Any]:
        """Extrae campos comunes del evento"""
        pass


class StripeMapper(BaseProviderMapper):
    """
    Mapper para eventos de Stripe

    Docs: https://stripe.com/docs/api/payment_intents/object
    """

    provider_name = "stripe"
    confidence_score = 0.85

    def can_handle(self, raw_event: dict[str, Any]) -> bool:
        """Detecta si es un evento de Stripe"""
        # Stripe usa "object" field y IDs con prefijos conocidos
        object_type = raw_event.get("object", "")
        stripe_id = raw_event.get("id", "")

        # Verificar que stripe_id sea string antes de usar startswith
        if not isinstance(stripe_id, str):
            stripe_id = str(stripe_id) if stripe_id else ""

        return object_type in [
            "payment_intent",
            "charge",
            "refund",
        ] or stripe_id.startswith(("pi_", "ch_", "re_"))

    def map_status(self, raw_event: dict[str, Any]) -> PaymentStatus:
        """
        Map Stripe statuses:
        - requires_payment_method, requires_confirmation → pending
        - processing → pending
        - succeeded → approved
        - canceled → cancelled
        - failed → failed
        """
        stripe_status = raw_event.get("status", "").lower()

        status_map = {
            "requires_payment_method": PaymentStatus.PENDING,
            "requires_confirmation": PaymentStatus.PENDING,
            "requires_action": PaymentStatus.PENDING,
            "processing": PaymentStatus.PENDING,
            "succeeded": PaymentStatus.APPROVED,
            "canceled": PaymentStatus.CANCELLED,
            "failed": PaymentStatus.FAILED,
        }

        return status_map.get(stripe_status, PaymentStatus.PENDING)

    def map_failure_reason(self, raw_event: dict[str, Any]) -> FailureReason | None:
        """
        Map Stripe error codes to FailureReason

        Stripe usa "last_payment_error.code" o "failure_code"
        """
        # Intentar extraer error code
        error_code = None

        if "last_payment_error" in raw_event:
            error_code = raw_event["last_payment_error"].get("code")
        elif "failure_code" in raw_event:
            error_code = raw_event.get("failure_code")

        if not error_code:
            return None

        # Mapeo de códigos Stripe → FailureReason
        stripe_error_map = {
            "card_declined": FailureReason.CARD_DECLINED,
            "insufficient_funds": FailureReason.INSUFFICIENT_FUNDS,
            "expired_card": FailureReason.EXPIRED_CARD,
            "incorrect_cvc": FailureReason.INVALID_CARD,
            "processing_error": FailureReason.PROVIDER_ERROR,
            "card_velocity_exceeded": FailureReason.SECURITY_VIOLATION,
            "fraudulent": FailureReason.FRAUD_SUSPECTED,
            "authentication_required": FailureReason.SECURITY_VIOLATION,
            "three_d_secure_failed": FailureReason.SECURITY_VIOLATION,
            "lost_card": FailureReason.BLOCKED_CARD,
            "stolen_card": FailureReason.BLOCKED_CARD,
            "blocked_card": FailureReason.BLOCKED_CARD,
        }

        return stripe_error_map.get(error_code, None)

    def extract_fields(self, raw_event: dict[str, Any]) -> dict[str, Any]:
        """
        Extrae campos de Stripe

        Fields:
        - id: payment intent ID
        - amount: en centavos (convertir a decimal)
        - currency: ISO 4217 lowercase
        - created: Unix timestamp
        - metadata.merchant_id
        """
        # Amount en Stripe está en centavos
        amount_cents = raw_event.get("amount", 0)
        amount = amount_cents / 100.0

        # Currency a uppercase
        currency = (raw_event.get("currency") or "USD").upper()

        # Timestamps (Unix → ISO)
        created_ts = raw_event.get("created")
        created_at = (
            datetime.fromtimestamp(created_ts, UTC).isoformat()
            if created_ts
            else datetime.now(UTC).isoformat()
        )

        # Merchant desde metadata
        metadata = raw_event.get("metadata", {})
        merchant_id = metadata.get("merchant_id") or metadata.get("merchant")

        return {
            "provider_transaction_id": raw_event.get("id"),
            "merchant_id": merchant_id,
            "amount": amount,
            "currency": currency,
            "country_code": None,  # Stripe no incluye country en PI
            "created_at": created_at,
            "updated_at": created_at,
        }


class AdyenMapper(BaseProviderMapper):
    """
    Mapper para eventos de Adyen

    Docs: https://docs.adyen.com/api-explorer/
    """

    provider_name = "adyen"
    confidence_score = 0.80

    def can_handle(self, raw_event: dict[str, Any]) -> bool:
        """Detecta eventos de Adyen"""
        # Adyen usa "pspReference" como ID único
        return "pspReference" in raw_event or raw_event.get("additionalData", {}).get(
            "paymentMethod"
        )

    def map_status(self, raw_event: dict[str, Any]) -> PaymentStatus:
        """
        Map Adyen result codes:
        - Authorised → approved
        - Refused, Error → failed
        - Cancelled → cancelled
        - Pending, Received → pending
        """
        result_code = raw_event.get("resultCode", "").lower()

        status_map = {
            "authorised": PaymentStatus.APPROVED,
            "refused": PaymentStatus.FAILED,
            "error": PaymentStatus.FAILED,
            "cancelled": PaymentStatus.CANCELLED,
            "pending": PaymentStatus.PENDING,
            "received": PaymentStatus.PENDING,
        }

        return status_map.get(result_code, PaymentStatus.PENDING)

    def map_failure_reason(self, raw_event: dict[str, Any]) -> FailureReason | None:
        """Map Adyen refusalReason"""
        refusal = raw_event.get("refusalReason", "").lower()

        if not refusal:
            return None

        # Mapeo simplificado (Adyen tiene 200+ códigos)
        if "fraud" in refusal or "security" in refusal:
            return FailureReason.FRAUD_SUSPECTED
        elif "insufficient" in refusal:
            return FailureReason.INSUFFICIENT_FUNDS
        elif "expired" in refusal:
            return FailureReason.EXPIRED_CARD
        elif "cvc" in refusal or "cvv" in refusal:
            return FailureReason.INVALID_CARD
        elif "3d" in refusal or "3ds" in refusal:
            return FailureReason.SECURITY_VIOLATION
        else:
            return FailureReason.CARD_DECLINED

    def extract_fields(self, raw_event: dict[str, Any]) -> dict[str, Any]:
        """Extrae campos de Adyen"""
        # Amount en Adyen tiene estructura {"currency": "EUR", "value": 1000}
        amount_data = raw_event.get("amount", {})
        amount_cents = amount_data.get("value", 0)
        amount = amount_cents / 100.0
        currency = amount_data.get("currency", "USD")

        # Merchant reference
        merchant_id = raw_event.get("merchantReference")

        return {
            "provider_transaction_id": raw_event.get("pspReference"),
            "merchant_id": merchant_id,
            "amount": amount,
            "currency": currency,
            "country_code": None,
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }


class MercadoPagoMapper(BaseProviderMapper):
    """
    Mapper para MercadoPago

    Docs: https://www.mercadopago.com.mx/developers/es/reference/payments/_payments_id/get
    """

    provider_name = "mercadopago"
    confidence_score = 0.80

    def can_handle(self, raw_event: dict[str, Any]) -> bool:
        """Detecta eventos de MercadoPago"""
        # MercadoPago usa "collector_id" o tiene "payment_method_id"
        return "collector_id" in raw_event or "payment_method_id" in raw_event

    def map_status(self, raw_event: dict[str, Any]) -> PaymentStatus:
        """
        Map MercadoPago statuses:
        - approved → approved
        - rejected → failed
        - pending → pending
        - cancelled → cancelled
        - refunded → refunded
        """
        mp_status = raw_event.get("status", "").lower()

        status_map = {
            "approved": PaymentStatus.APPROVED,
            "rejected": PaymentStatus.FAILED,
            "pending": PaymentStatus.PENDING,
            "in_process": PaymentStatus.PENDING,
            "cancelled": PaymentStatus.CANCELLED,
            "refunded": PaymentStatus.REFUNDED,
        }

        return status_map.get(mp_status, PaymentStatus.PENDING)

    def map_failure_reason(self, raw_event: dict[str, Any]) -> FailureReason | None:
        """Map MercadoPago status_detail"""
        detail = raw_event.get("status_detail", "").lower()

        if not detail or raw_event.get("status") != "rejected":
            return None

        detail_map = {
            "cc_rejected_insufficient_amount": FailureReason.INSUFFICIENT_FUNDS,
            "cc_rejected_bad_filled_security_code": FailureReason.INVALID_CARD,
            "cc_rejected_blacklist": FailureReason.BLOCKED_CARD,
            "cc_rejected_high_risk": FailureReason.FRAUD_SUSPECTED,
            "cc_rejected_call_for_authorize": FailureReason.SECURITY_VIOLATION,
        }

        return detail_map.get(detail, FailureReason.CARD_DECLINED)

    def extract_fields(self, raw_event: dict[str, Any]) -> dict[str, Any]:
        """Extrae campos de MercadoPago"""
        return {
            "provider_transaction_id": str(raw_event.get("id")),
            "merchant_id": str(raw_event.get("collector_id")),
            "amount": float(raw_event.get("transaction_amount", 0)),
            "currency": (raw_event.get("currency_id") or "USD").upper(),
            "country_code": None,
            "created_at": raw_event.get("date_created", datetime.now(UTC).isoformat()),
            "updated_at": raw_event.get("date_last_updated", datetime.now(UTC).isoformat()),
        }


# ============================================================================
# RULE-BASED NORMALIZER
# ============================================================================


class RuleBasedNormalizer(INormalizer):
    """
    Normalizer basado en reglas para providers conocidos

    Ventajas:
    - Sin costo de IA
    - Latencia muy baja (<10ms)
    - Determinístico 100%
    - Sin dependencia de APIs externas

    Desventajas:
    - Solo funciona para providers mapeados
    - Requiere mantenimiento manual
    - Menos flexible que IA

    Ejemplo:
        ```python
        normalizer = RuleBasedNormalizer()

        stripe_event = {
            "id": "pi_123",
            "object": "payment_intent",
            "amount": 5000,
            "status": "succeeded"
        }

        if normalizer.can_normalize(stripe_event):
            normalized = normalizer.normalize(stripe_event)
            # normalized.normalization_method == NormalizationMethod.RULE_BASED
            # normalized.confidence_score == 0.85 (alta confianza)
        ```
    """

    def __init__(self):
        """Inicializa con mappers de providers conocidos"""
        self._mappers: list[BaseProviderMapper] = [
            StripeMapper(),
            AdyenMapper(),
            MercadoPagoMapper(),
        ]

        logger.info(
            "RuleBasedNormalizer initialized",
            extra={"supported_providers": [m.provider_name for m in self._mappers]},
        )

    def can_normalize(self, raw_event: dict[str, Any]) -> bool:
        """
        Verifica si algún mapper puede procesar el evento

        Args:
            raw_event: Evento crudo del provider

        Returns:
            True si hay un mapper que reconoce el evento
        """
        return self._get_mapper(raw_event) is not None

    def _get_mapper(self, raw_event: dict[str, Any]) -> BaseProviderMapper | None:
        """
        Selecciona el mapper apropiado para el evento

        Factory pattern: itera mappers hasta encontrar uno compatible

        Args:
            raw_event: Evento a procesar

        Returns:
            Mapper compatible o None si no hay match
        """
        for mapper in self._mappers:
            if mapper.can_handle(raw_event):
                logger.debug(
                    "Mapper selected",
                    extra={"provider": mapper.provider_name},
                )
                return mapper

        logger.debug("No mapper found for event")
        return None

    def normalize(self, raw_event: dict[str, Any]) -> NormalizedPaymentEvent:
        """
        Normaliza evento usando reglas del provider

        Args:
            raw_event: Evento crudo

        Returns:
            NormalizedPaymentEvent

        Raises:
            NormalizationException: Si no hay mapper compatible
        """
        start_time = datetime.now(UTC)

        # Seleccionar mapper
        mapper = self._get_mapper(raw_event)
        if not mapper:
            raise NormalizationException(
                "No rule-based mapper available for this event. Use AI-based normalizer instead."
            )

        try:
            # Aplicar reglas de mapeo
            status_category = mapper.map_status(raw_event)
            failure_reason = mapper.map_failure_reason(raw_event)
            fields = mapper.extract_fields(raw_event)

            # Calcular latencia
            end_time = datetime.now(UTC)
            latency_ms = int((end_time - start_time).total_seconds() * 1000)

            # Calcular USD equivalent para analytics
            amount_usd_equivalent = convert_to_usd(fields["amount"], fields["currency"])

            # Crear evento normalizado con campos correctos del modelo
            normalized_event = NormalizedPaymentEvent(
                # Core fields
                merchant_name=fields.get("merchant_id") or "unknown_merchant",
                provider=mapper.provider_name,
                country=fields.get("country_code") or "XX",
                # Status
                status_category=status_category,
                failure_reason=failure_reason,
                # Financial - preservar original + USD equivalent
                amount=fields["amount"],
                currency=fields["currency"],
                amount_usd_equivalent=amount_usd_equivalent,
                # Provider details
                provider_transaction_id=fields["provider_transaction_id"],
                provider_status=raw_event.get("status"),  # Original status from provider
                latency_ms=fields.get("latency_ms"),
                # Normalization metadata
                normalization_method=NormalizationMethod.RULE_BASED,
                confidence_score=mapper.confidence_score,
                # Raw data preservation
                raw_data=raw_event,
                event_metadata={
                    "normalization_timestamp": datetime.now(UTC).isoformat(),
                    "mapper_used": mapper.provider_name,
                    "normalization_latency_ms": latency_ms,
                },
            )

            logger.info(
                "Rule-based normalization successful",
                extra={
                    "provider": mapper.provider_name,
                    "transaction_id": fields["provider_transaction_id"],
                    "status": status_category.value,
                    "latency_ms": latency_ms,
                },
            )

            return normalized_event

        except Exception as e:
            logger.error(
                "Rule-based normalization failed",
                extra={
                    "provider": mapper.provider_name if mapper else None,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise NormalizationException(f"Rule-based normalization error: {e}") from e
