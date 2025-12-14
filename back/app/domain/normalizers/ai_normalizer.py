"""
AI-Based Payment Normalizer

Normaliza eventos de pago usando OpenAI + LangChain con structured output.

Design Principles:
- Retry logic con exponential backoff (tenacity)
- Error handling específico para casos de OpenAI
- Logging estructurado de cada normalización
- Confidence score calculado basado en respuesta
- Type-safe con Pydantic schemas

Architecture:
- Implementa INormalizer Protocol
- Usa LangChainClient para abstracción de IA
- Sistema de prompts versionados
- Manejo robusto de errores (timeout, rate limit, etc.)
"""

import json
import logging
from datetime import UTC, datetime
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from openai import APIError, APITimeoutError, RateLimitError
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.domain.exceptions import (
    AIServiceException,
    NormalizationException,
    NormalizationTimeoutException,
    RateLimitExceededException,
)
from app.domain.interfaces.normalizer import INormalizer
from app.domain.models.enums import NormalizationMethod
from app.domain.models.payment_event import NormalizedPaymentEvent
from app.domain.utils.currency_converter import convert_to_usd
from app.infraestructure.ai.langchain_client import LangChainClient
from app.infraestructure.ai.schemas import AIPaymentNormalizationOutput
from app.infraestructure.ai.system_prompts import (
    PAYMENT_NORMALIZATION_SYSTEM_PROMPT,
)
from app.infraestructure.core.config import settings

logger = logging.getLogger(__name__)


class AIBasedNormalizer(INormalizer):
    """
    Normalizer basado en IA (OpenAI GPT-4o-mini)

    Usa LangChain con structured output para normalizar eventos
    de cualquier payment provider a nuestro schema estándar.

    Features:
    - Retry automático con exponential backoff (3 intentos)
    - Manejo de rate limits y timeouts
    - Validación automática vía Pydantic
    - Logging detallado para debugging
    - Confidence score alto (0.95) por defecto

    Ejemplo:
        ```python
        normalizer = AIBasedNormalizer()

        raw_event = {
            "id": "pi_123",
            "amount": 5000,
            "currency": "usd",
            "status": "succeeded"
        }

        normalized = normalizer.normalize(raw_event)
        print(normalized.status)  # PaymentStatus.SUCCEEDED
        print(normalized.confidence_score)  # 0.95
        ```
    """

    def __init__(
        self,
        langchain_client: LangChainClient | None = None,
    ) -> None:
        """
        Inicializa el normalizer

        Args:
            langchain_client: Cliente de LangChain (opcional, para testing)
                            Si no se provee, se crea uno nuevo
        """
        self._client = langchain_client or LangChainClient()
        self._structured_llm = self._client.get_structured_llm(AIPaymentNormalizationOutput)

        logger.info(
            "AIBasedNormalizer initialized",
            extra={
                "model": settings.OPENAI_MODEL,
                "max_retries": settings.AI_MAX_RETRIES,
            },
        )

    def can_normalize(self, raw_event: dict[str, Any]) -> bool:
        """
        Verifica si este normalizer puede procesar el evento

        AIBasedNormalizer puede procesar CUALQUIER evento,
        por lo que siempre retorna True (es el fallback universal).

        Args:
            raw_event: Evento crudo desde el provider

        Returns:
            True siempre (AI puede intentar normalizar cualquier cosa)

        Note:
            En un sistema con múltiples normalizers, este sería
            el último en la cadena (catch-all).
        """
        return True

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((RateLimitError, APITimeoutError, APIError)),
        reraise=True,
    )
    def _normalize_with_retry(self, raw_event: dict[str, Any]) -> AIPaymentNormalizationOutput:
        """
        Normaliza con retry logic automático

        Retry strategy:
        - 3 intentos máximo
        - Backoff exponencial: 2s, 4s, 8s
        - Solo reintenta en errores transitorios (rate limit, timeout, API error)
        - NO reintenta en ValidationError (error de schema)

        Args:
            raw_event: Evento crudo a normalizar

        Returns:
            Schema normalizado y validado

        Raises:
            RateLimitError: Después de 3 intentos con rate limit
            APITimeoutError: Después de 3 intentos con timeout
            ValidationError: Si el output del LLM no cumple el schema
        """
        # Preparar mensajes para el LLM
        messages = [
            SystemMessage(content=PAYMENT_NORMALIZATION_SYSTEM_PROMPT),
            HumanMessage(
                content=f"Normalize this payment event:\n\n{json.dumps(raw_event, indent=2)}"
            ),
        ]

        logger.debug(
            "Invoking AI normalization",
            extra={
                "raw_event_keys": list(raw_event.keys()),
                "event_size_bytes": len(json.dumps(raw_event)),
            },
        )

        # Invocar LLM con structured output
        result: AIPaymentNormalizationOutput = self._client.invoke_with_logging(
            structured_llm=self._structured_llm,
            messages=messages,
            context={"provider": raw_event.get("provider", "unknown")},
        )

        return result

    def normalize(self, raw_event: dict[str, Any]) -> NormalizedPaymentEvent:
        """
        Normaliza un evento de pago usando IA

        Process:
        1. Invoca LLM con structured output (con retry automático)
        2. Valida resultado con Pydantic (AIPaymentNormalizationOutput)
        3. Convierte currency a USD
        4. Mapea a NormalizedPaymentEvent (SQLModel)
        5. Enriquece con metadata de normalización

        Args:
            raw_event: Evento crudo del payment provider
                      Puede tener cualquier estructura

        Returns:
            NormalizedPaymentEvent listo para persistir

        Raises:
            RateLimitExceededException: Si se excede rate limit después de retries
            NormalizationTimeoutException: Si timeout después de retries
            AIServiceException: Para otros errores de IA
            NormalizationException: Para errores de validación/parsing

        Ejemplo:
            ```python
            raw_event = {
                "transaction_id": "TXN-999",
                "amount_cents": 15000,
                "status": "DECLINED",
                "error": "insufficient_funds"
            }

            normalized = normalizer.normalize(raw_event)
            # normalized.status_category == PaymentStatus.FAILED
            # normalized.failure_reason == FailureReason.INSUFFICIENT_FUNDS
            # normalized.normalization_method == NormalizationMethod.AI_BASED
            ```
        """
        start_time = datetime.now(UTC)

        try:
            # Normalización con retry automático
            ai_output = self._normalize_with_retry(raw_event)

            # Calcular latencia de normalización
            end_time = datetime.now(UTC)
            normalization_latency = int((end_time - start_time).total_seconds() * 1000)

            # Calcular USD equivalent para analytics (solo si hay amount y currency)
            amount_usd_equivalent = None
            if ai_output.amount is not None and ai_output.currency is not None:
                amount_usd_equivalent = convert_to_usd(ai_output.amount, ai_output.currency)

            # Mapear AI output a NormalizedPaymentEvent
            normalized_event = NormalizedPaymentEvent(
                # Core fields
                merchant_name=ai_output.merchant_name or "unknown_merchant",
                provider=ai_output.provider.lower(),
                country=ai_output.country or "XX",  # Default country code
                transactional_id=raw_event.get("transactional_id"),  # From Data Lake
                # Status
                status_category=ai_output.status_category,
                failure_reason=ai_output.failure_reason,
                error_source=ai_output.error_source,  # For intelligent alerts
                http_status_code=ai_output.http_status_code,  # For coherence validation
                # Financial (preserve original currency) - may be None for error events
                amount=ai_output.amount,
                currency=ai_output.currency.upper() if ai_output.currency else None,
                amount_usd_equivalent=amount_usd_equivalent,
                # Provider details
                provider_transaction_id=ai_output.provider_transaction_id,
                provider_status=ai_output.provider_status,
                latency_ms=ai_output.latency_ms,
                # Normalization metadata
                normalization_method=NormalizationMethod.AI_BASED,
                confidence_score=0.95,  # Alta confianza en IA
                # Raw data preservation
                raw_data=raw_event,
                event_metadata={
                    "normalization_timestamp": datetime.now(UTC).isoformat(),
                    "model_used": settings.OPENAI_MODEL,
                    "prompt_version": "1.0.0",
                    "normalization_latency_ms": normalization_latency,
                },
            )

            logger.info(
                "AI normalization successful",
                extra={
                    "provider": normalized_event.provider,
                    "transaction_id": normalized_event.provider_transaction_id,
                    "status": normalized_event.status_category.value,
                    "latency_ms": normalization_latency,
                },
            )

            return normalized_event

        except RateLimitError as e:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "error": str(e),
                    "raw_event_sample": str(raw_event)[:100],
                },
            )
            raise RateLimitExceededException(
                f"OpenAI rate limit exceeded: {e}",
                retry_after=getattr(e, "retry_after", None),
            ) from e

        except APITimeoutError as e:
            logger.error(
                "AI normalization timeout",
                extra={
                    "timeout_seconds": settings.AI_TIMEOUT_SECONDS,
                    "error": str(e),
                },
            )
            raise NormalizationTimeoutException(
                f"AI normalization timed out after {settings.AI_TIMEOUT_SECONDS}s",
                timeout_seconds=settings.AI_TIMEOUT_SECONDS,
            ) from e

        except (APIError, Exception) as e:
            # APIError: errores de OpenAI (model not available, API down, etc.)
            # Exception: catch-all para otros errores inesperados
            logger.error(
                "AI normalization failed",
                extra={
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "raw_event_sample": str(raw_event)[:200],
                },
                exc_info=True,
            )

            if isinstance(e, ValidationError):
                raise NormalizationException(f"AI output validation failed: {e}") from e

            raise AIServiceException(f"AI service error: {type(e).__name__} - {e}") from e
