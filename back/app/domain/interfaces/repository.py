"""Interface (Protocol) para repositorio de eventos de pago"""

from typing import Protocol
from uuid import UUID

from app.domain.models.enums import PaymentStatus
from app.domain.models.payment_event import NormalizedPaymentEvent


class IPaymentRepository(Protocol):
    """
    Protocol para repositorio de eventos de pago normalizados

    Define el contrato para operaciones de persistencia de eventos.
    Permite múltiples implementaciones (SQL, NoSQL, in-memory para tests, etc.)

    Best Practice: Usar Protocol para desacoplamiento entre domain y infrastructure
    """

    def save(self, event: NormalizedPaymentEvent) -> NormalizedPaymentEvent:
        """
        Guarda un evento de pago normalizado

        Args:
            event: Evento a guardar

        Returns:
            Evento guardado con ID y timestamps generados

        Raises:
            RepositoryException: Si hay error al guardar
        """
        ...

    def get_by_id(self, event_id: UUID) -> NormalizedPaymentEvent | None:
        """
        Obtiene un evento por su ID

        Args:
            event_id: UUID del evento

        Returns:
            Evento si existe, None en caso contrario
        """
        ...

    def get_by_provider_transaction_id(
        self, provider_transaction_id: str
    ) -> NormalizedPaymentEvent | None:
        """
        Busca evento por ID de transacción del proveedor

        Args:
            provider_transaction_id: ID de transacción del proveedor

        Returns:
            Evento si existe, None en caso contrario

        Note:
            Útil para detectar duplicados y reconciliación
        """
        ...

    def get_unprocessed(self, limit: int = 100) -> list[NormalizedPaymentEvent]:
        """
        Obtiene eventos que no pudieron ser procesados (UNPROCESSED)

        Args:
            limit: Número máximo de eventos a retornar

        Returns:
            Lista de eventos sin procesar

        Note:
            Usado por workers de retry para reintentar normalización
        """
        ...

    def get_by_filters(
        self,
        provider: str | None = None,
        status: PaymentStatus | None = None,
        merchant_name: str | None = None,
        country: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[NormalizedPaymentEvent]:
        """
        Busca eventos con filtros opcionales

        Args:
            provider: Filtrar por proveedor
            status: Filtrar por estado
            merchant_name: Filtrar por nombre de comercio
            country: Filtrar por país
            limit: Número máximo de resultados
            offset: Offset para paginación

        Returns:
            Lista de eventos que cumplen los filtros
        """
        ...

    def count_by_status(self, status: PaymentStatus) -> int:
        """
        Cuenta eventos por estado

        Args:
            status: Estado a contar

        Returns:
            Número de eventos con ese estado

        Note:
            Útil para métricas y analytics
        """
        ...
