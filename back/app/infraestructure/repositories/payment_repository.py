"""
Payment Repository Implementation

Implementación concreta del repositorio de eventos de pago.
Usa SQLModel Session (sync) para interactuar con PostgreSQL.
"""

import logging
from typing import Any
from uuid import UUID

from sqlmodel import Session, select

from app.domain.interfaces.repository import IPaymentRepository
from app.domain.models.enums import PaymentStatus
from app.domain.models.payment_event import NormalizedPaymentEvent

logger = logging.getLogger(__name__)


class PaymentRepository(IPaymentRepository):
    """
    Repositorio para persistencia de eventos de pago normalizados

    Implementa IPaymentRepository usando SQLModel (sync).
    Todas las operaciones son sincrónicas - la DB usa SessionDep (sync).
    """

    def __init__(self, session: Session) -> None:
        """
        Inicializa el repositorio

        Args:
            session: SQLModel Session (sync) inyectada por FastAPI
        """
        self.session = session

    def save(self, event: NormalizedPaymentEvent) -> NormalizedPaymentEvent:
        """
        Persiste un evento normalizado en la base de datos

        Args:
            event: Evento normalizado a guardar

        Returns:
            Evento guardado con ID y timestamps generados

        Ejemplo:
            ```python
            repo = PaymentRepository(session)
            event = NormalizedPaymentEvent(...)
            saved = repo.save(event)
            print(saved.id)  # UUID generado
            ```
        """
        self.session.add(event)
        self.session.commit()
        self.session.refresh(event)

        logger.info(
            "Payment event saved",
            extra={
                "event_id": str(event.id),
                "merchant": event.merchant_name,
                "provider": event.provider,
                "status": event.status_category.value,
                "amount": float(event.amount),
                "currency": event.currency,
            },
        )

        return event

    def get_by_id(self, event_id: UUID) -> NormalizedPaymentEvent | None:
        """
        Busca un evento por su ID

        Args:
            event_id: UUID del evento

        Returns:
            Evento encontrado o None si no existe

        Ejemplo:
            ```python
            event = repo.get_by_id(uuid.uuid4())
            if event:
                print(event.merchant_name)
            ```
        """
        statement = select(NormalizedPaymentEvent).where(NormalizedPaymentEvent.id == event_id)
        result = self.session.exec(statement)
        event = result.one_or_none()

        if event:
            logger.debug(
                "Payment event retrieved",
                extra={"event_id": str(event_id), "found": True},
            )
        else:
            logger.debug(
                "Payment event not found",
                extra={"event_id": str(event_id), "found": False},
            )

        return event

    def get_by_provider_transaction_id(
        self, provider_transaction_id: str
    ) -> NormalizedPaymentEvent | None:
        """
        Busca evento por ID de transacción del proveedor

        Args:
            provider_transaction_id: ID de transacción del proveedor

        Returns:
            Evento si existe, None en caso contrario
        """
        statement = select(NormalizedPaymentEvent).where(
            NormalizedPaymentEvent.provider_transaction_id == provider_transaction_id
        )
        result = self.session.exec(statement)
        return result.one_or_none()

    def get_unprocessed(self, limit: int = 100) -> list[NormalizedPaymentEvent]:
        """
        Obtiene eventos que no pudieron ser procesados (UNPROCESSED)

        Args:
            limit: Número máximo de eventos a retornar

        Returns:
            Lista de eventos sin procesar
        """
        statement = (
            select(NormalizedPaymentEvent)
            .where(NormalizedPaymentEvent.status_category == PaymentStatus.UNPROCESSED)
            .limit(limit)
        )
        result = self.session.exec(statement)
        return list(result.all())

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
        statement = select(NormalizedPaymentEvent)

        if provider:
            statement = statement.where(NormalizedPaymentEvent.provider == provider)
        if status:
            statement = statement.where(NormalizedPaymentEvent.status_category == status)
        if merchant_name:
            statement = statement.where(NormalizedPaymentEvent.merchant_name == merchant_name)
        if country:
            statement = statement.where(NormalizedPaymentEvent.country == country)

        statement = statement.limit(limit).offset(offset)
        result = self.session.exec(statement)
        return list(result.all())

    def count_by_status(self, status: PaymentStatus) -> int:
        """
        Cuenta eventos por estado

        Args:
            status: Estado a contar

        Returns:
            Número de eventos con ese estado
        """
        statement = select(NormalizedPaymentEvent).where(
            NormalizedPaymentEvent.status_category == status
        )
        result = self.session.exec(statement)
        return len(list(result.all()))

    def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> list[NormalizedPaymentEvent]:
        """
        Obtiene lista de eventos con paginación y filtros opcionales

        Args:
            limit: Número máximo de eventos a retornar
            offset: Número de eventos a saltar
            filters: Filtros opcionales (provider, status_category, etc.)

        Returns:
            Lista de eventos paginados

        Ejemplo:
            ```python
            # Primeros 50 eventos
            events = repo.get_all(limit=50)

            # Eventos de Stripe aprobados
            events = repo.get_all(
                filters={"provider": "stripe", "status_category": "APPROVED"}
            )
            ```
        """
        statement = select(NormalizedPaymentEvent)

        # Aplicar filtros si existen
        if filters:
            for key, value in filters.items():
                if hasattr(NormalizedPaymentEvent, key):
                    statement = statement.where(getattr(NormalizedPaymentEvent, key) == value)

        # Paginación
        statement = statement.limit(limit).offset(offset)

        result = self.session.exec(statement)
        events = result.all()

        logger.debug(
            "Payment events retrieved",
            extra={
                "count": len(events),
                "limit": limit,
                "offset": offset,
                "filters": filters,
            },
        )

        return list(events)

    def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Cuenta eventos con filtros opcionales

        Args:
            filters: Filtros opcionales

        Returns:
            Número total de eventos que cumplen los filtros

        Ejemplo:
            ```python
            total = repo.count()
            failed = repo.count(filters={"status_category": "FAILED"})
            ```
        """
        statement = select(NormalizedPaymentEvent)

        if filters:
            for key, value in filters.items():
                if hasattr(NormalizedPaymentEvent, key):
                    statement = statement.where(getattr(NormalizedPaymentEvent, key) == value)

        result = self.session.exec(statement)
        events = result.all()
        count = len(events)

        logger.debug(
            "Payment events counted",
            extra={"count": count, "filters": filters},
        )

        return count
