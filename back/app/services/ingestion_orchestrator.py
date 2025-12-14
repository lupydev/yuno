"""
Ingestion Orchestrator Service

Coordina el proceso completo de ingestión de eventos:
1. Selección de estrategia de normalización (AI vs Rule-based)
2. Normalización del evento
3. Persistencia en base de datos
4. Manejo de errores y fallbacks
"""

import logging
from typing import Any

from app.domain.exceptions import NormalizationException
from app.domain.interfaces.normalizer import INormalizer
from app.domain.interfaces.repository import IPaymentRepository
from app.domain.models.payment_event import NormalizedPaymentEvent
from app.domain.normalizers.ai_normalizer import AIBasedNormalizer
from app.domain.normalizers.rule_normalizer import RuleBasedNormalizer

logger = logging.getLogger(__name__)


class IngestionOrchestrator:
    """
    Orquestador del flujo de ingestión de eventos de pago

    Responsabilidades:
    - Seleccionar estrategia de normalización apropiada
    - Ejecutar normalización con fallback automático
    - Persistir evento normalizado
    - Manejo robusto de errores

    Strategy Pattern: Decide dinámicamente qué normalizer usar
    """

    def __init__(
        self,
        repository: IPaymentRepository,
        rule_normalizer: RuleBasedNormalizer,
        ai_normalizer: AIBasedNormalizer,
    ) -> None:
        """
        Inicializa el orchestrator

        Args:
            repository: Repositorio para persistencia
            rule_normalizer: Normalizer basado en reglas
            ai_normalizer: Normalizer basado en IA
        """
        self.repository = repository
        self.rule_normalizer = rule_normalizer
        self.ai_normalizer = ai_normalizer

        logger.info(
            "IngestionOrchestrator initialized",
            extra={
                "rule_normalizer": type(rule_normalizer).__name__,
                "ai_normalizer": type(ai_normalizer).__name__,
            },
        )

    def _select_normalizer(self, raw_event: dict[str, Any]) -> INormalizer:
        """
        Selecciona el normalizer apropiado usando Strategy Pattern

        Decision tree:
        1. Intenta rule-based si puede reconocer el formato
        2. Fallback a AI-based si no hay regla disponible

        Args:
            raw_event: Evento crudo del provider

        Returns:
            Normalizer seleccionado (rule-based o AI-based)
        """
        # Intentar rule-based primero (más rápido y barato)
        if self.rule_normalizer.can_normalize(raw_event):
            logger.info(
                "Normalizer selected: RULE-BASED",
                extra={"reason": "Event matches known provider pattern"},
            )
            return self.rule_normalizer

        # Fallback a AI (puede normalizar cualquier cosa)
        logger.info(
            "Normalizer selected: AI-BASED",
            extra={"reason": "No rule-based mapper available, using AI fallback"},
        )
        return self.ai_normalizer

    def ingest(
        self,
        raw_event: dict[str, Any],
        provider_hint: str | None = None,
    ) -> NormalizedPaymentEvent:
        """
        Procesa e ingesta un evento de pago

        Flujo completo:
        1. Seleccionar normalizer (rule-based vs AI)
        2. Normalizar evento
        3. Persistir en base de datos
        4. Retornar evento guardado

        Args:
            raw_event: Evento crudo del provider (cualquier formato)
            provider_hint: Hint opcional del provider (stripe, adyen, etc.)

        Returns:
            Evento normalizado y persistido

        Raises:
            NormalizationException: Si la normalización falla
            Exception: Para otros errores inesperados

        Ejemplo:
            ```python
            orchestrator = IngestionOrchestrator(repo, rule_norm, ai_norm)

            raw_event = {
                "id": "ch_123",
                "amount": 5000,
                "currency": "usd",
                "status": "succeeded"
            }

            event = orchestrator.ingest(raw_event)
            print(event.id)  # UUID generado
            print(event.normalization_method)  # "RULE_BASED" o "AI_BASED"
            ```
        """
        logger.info(
            "Ingestion started",
            extra={
                "provider_hint": provider_hint,
                "event_keys": list(raw_event.keys()),
            },
        )

        try:
            # 1. Seleccionar estrategia de normalización
            normalizer = self._select_normalizer(raw_event)

            # 2. Normalizar evento
            logger.debug("Starting normalization...")
            normalized_event = normalizer.normalize(raw_event)

            # 3. Persistir en base de datos
            logger.debug("Persisting normalized event...")
            saved_event = self.repository.save(normalized_event)

            logger.info(
                "Ingestion completed successfully",
                extra={
                    "event_id": str(saved_event.id),
                    "normalizer": type(normalizer).__name__,
                    "status": saved_event.status_category.value,
                    "merchant": saved_event.merchant_name,
                },
            )

            return saved_event

        except NormalizationException as e:
            logger.error(
                "Normalization failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise

        except Exception as e:
            logger.error(
                "Unexpected error during ingestion",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            raise
