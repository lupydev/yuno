"""Interface (Protocol) para normalizadores de eventos de pago"""

from typing import Protocol

from app.domain.schemas.normalization_schemas import NormalizedPaymentSchema


class INormalizer(Protocol):
    """
    Protocol para normalizadores de eventos de pago

    Define el contrato que deben cumplir todos los normalizadores
    (AI-based, Rule-based, Hybrid, etc.)

    Best Practice: Usar Protocol en vez de ABC para dependency injection
    más flexible y testing más fácil.
    """

    async def normalize(self, raw_event: dict) -> NormalizedPaymentSchema:
        """
        Normaliza un evento crudo a formato estructurado

        Args:
            raw_event: Evento de pago en formato original del proveedor

        Returns:
            NormalizedPaymentSchema con datos normalizados

        Raises:
            NormalizationException: Si no se puede normalizar el evento
        """
        ...

    def can_normalize(self, raw_event: dict) -> bool:
        """
        Verifica si este normalizador puede procesar el evento

        Args:
            raw_event: Evento de pago a verificar

        Returns:
            True si puede normalizar, False en caso contrario

        Note:
            Útil para chain of responsibility pattern con múltiples normalizadores
        """
        ...
