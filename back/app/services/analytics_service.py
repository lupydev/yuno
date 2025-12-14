"""
Analytics Service

Servicio de analítica para métricas y reportes de pagos normalizados.
Provee insights sobre success rate, failure reasons, provider performance, etc.
"""

import logging
from datetime import datetime
from typing import Any

from sqlmodel import Session, func, select

from app.domain.models.enums import PaymentStatus
from app.domain.models.payment_event import NormalizedPaymentEvent

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Servicio de analítica para eventos de pago

    Provee métricas agregadas, estadísticas por provider,
    y análisis de errores para observabilidad.
    """

    def __init__(self, session: Session) -> None:
        """
        Inicializa el servicio de analítica

        Args:
            session: SQLModel Session (sync) inyectada por FastAPI
        """
        self.session = session

    def get_metrics_summary(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Retorna métricas agregadas del sistema

        Incluye:
        - Total de eventos
        - Distribución por status
        - Success rate general
        - Top failure reasons
        - Distribución por provider
        - Volumen transaccional (USD)

        Args:
            start_date: Fecha inicio (opcional)
            end_date: Fecha fin (opcional)

        Returns:
            Dict con métricas agregadas
        """
        # Base query
        query = select(NormalizedPaymentEvent)

        # Filtros de fecha
        if start_date:
            query = query.where(NormalizedPaymentEvent.created_at >= start_date)
        if end_date:
            query = query.where(NormalizedPaymentEvent.created_at <= end_date)

        # Total eventos
        total_events = self.session.exec(select(func.count()).select_from(query.subquery())).one()

        # Distribución por status
        status_distribution = self._get_status_distribution(start_date, end_date)

        # Success rate
        success_rate = self._calculate_success_rate(status_distribution, total_events)

        # Top failure reasons
        top_failures = self._get_top_failure_reasons(start_date, end_date, limit=5)

        # Distribución por provider
        provider_stats = self._get_provider_distribution(start_date, end_date)

        # Volumen transaccional
        volume = self._get_transaction_volume(start_date, end_date)

        # Error sources distribution
        error_sources = self._get_error_source_distribution(start_date, end_date)

        logger.info(
            "Metrics summary generated",
            extra={
                "total_events": total_events,
                "success_rate": success_rate,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
        )

        return {
            "total_events": total_events,
            "success_rate": success_rate,
            "status_distribution": status_distribution,
            "top_failure_reasons": top_failures,
            "provider_distribution": provider_stats,
            "transaction_volume_usd": volume,
            "error_source_distribution": error_sources,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

    def get_provider_stats(
        self,
        provider: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Retorna estadísticas específicas de un provider

        Args:
            provider: Nombre del provider (stripe, adyen, etc)
            start_date: Fecha inicio (opcional)
            end_date: Fecha fin (opcional)

        Returns:
            Dict con estadísticas del provider
        """
        # Base query filtrada por provider
        query = select(NormalizedPaymentEvent).where(
            NormalizedPaymentEvent.provider == provider.lower()
        )

        if start_date:
            query = query.where(NormalizedPaymentEvent.created_at >= start_date)
        if end_date:
            query = query.where(NormalizedPaymentEvent.created_at <= end_date)

        # Total eventos del provider
        total_events = self.session.exec(select(func.count()).select_from(query.subquery())).one()

        if total_events == 0:
            return {
                "provider": provider,
                "total_events": 0,
                "message": "No events found for this provider",
            }

        # Status distribution
        status_dist = self._get_status_distribution(start_date, end_date, provider)

        # Success rate
        success_rate = self._calculate_success_rate(status_dist, total_events)

        # Failure reasons específicos
        failures = self._get_top_failure_reasons(start_date, end_date, provider, limit=10)

        # Volumen
        volume = self._get_transaction_volume(start_date, end_date, provider)

        # Average latency (si existe metadata con timing)
        avg_latency = self._get_avg_latency(provider, start_date, end_date)

        # Error sources
        error_sources = self._get_error_source_distribution(start_date, end_date, provider)

        logger.info(
            "Provider stats generated",
            extra={
                "provider": provider,
                "total_events": total_events,
                "success_rate": success_rate,
            },
        )

        return {
            "provider": provider,
            "total_events": total_events,
            "success_rate": success_rate,
            "status_distribution": status_dist,
            "failure_reasons": failures,
            "transaction_volume_usd": volume,
            "average_latency_ms": avg_latency,
            "error_source_distribution": error_sources,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

    def get_failure_analysis(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Análisis detallado de fallos

        Args:
            start_date: Fecha inicio
            end_date: Fecha fin
            limit: Número máximo de resultados

        Returns:
            Dict con análisis de fallos
        """
        # Top failure reasons con counts
        top_reasons = self._get_top_failure_reasons(start_date, end_date, limit=limit)

        # Error sources breakdown
        error_sources = self._get_error_source_distribution(start_date, end_date)

        # HTTP status codes distribution (para fallos)
        http_codes = self._get_http_status_distribution(start_date, end_date)

        return {
            "top_failure_reasons": top_reasons,
            "error_source_distribution": error_sources,
            "http_status_codes": http_codes,
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
        }

    # Private helper methods

    def _get_status_distribution(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider: str | None = None,
    ) -> dict[str, int]:
        """Obtiene distribución de eventos por status"""
        query = select(
            NormalizedPaymentEvent.status_category,
            func.count(NormalizedPaymentEvent.id).label("count"),
        ).group_by(NormalizedPaymentEvent.status_category)

        if start_date:
            query = query.where(NormalizedPaymentEvent.created_at >= start_date)
        if end_date:
            query = query.where(NormalizedPaymentEvent.created_at <= end_date)
        if provider:
            query = query.where(NormalizedPaymentEvent.provider == provider.lower())

        results = self.session.exec(query).all()

        return {status.value: count for status, count in results}

    def _calculate_success_rate(self, status_distribution: dict[str, int], total: int) -> float:
        """Calcula success rate basado en distribución de status"""
        if total == 0:
            return 0.0

        approved_count = status_distribution.get(PaymentStatus.APPROVED.value, 0)
        return round((approved_count / total) * 100, 2)

    def _get_top_failure_reasons(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Obtiene top failure reasons con counts"""
        query = (
            select(
                NormalizedPaymentEvent.failure_reason,
                func.count(NormalizedPaymentEvent.id).label("count"),
            )
            .where(NormalizedPaymentEvent.failure_reason.isnot(None))
            .group_by(NormalizedPaymentEvent.failure_reason)
            .order_by(func.count(NormalizedPaymentEvent.id).desc())
            .limit(limit)
        )

        if start_date:
            query = query.where(NormalizedPaymentEvent.created_at >= start_date)
        if end_date:
            query = query.where(NormalizedPaymentEvent.created_at <= end_date)
        if provider:
            query = query.where(NormalizedPaymentEvent.provider == provider.lower())

        results = self.session.exec(query).all()

        return [
            {"reason": reason.value if reason else "unknown", "count": count}
            for reason, count in results
        ]

    def _get_provider_distribution(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Obtiene distribución de eventos por provider"""
        query = (
            select(
                NormalizedPaymentEvent.provider,
                func.count(NormalizedPaymentEvent.id).label("count"),
            )
            .group_by(NormalizedPaymentEvent.provider)
            .order_by(func.count(NormalizedPaymentEvent.id).desc())
        )

        if start_date:
            query = query.where(NormalizedPaymentEvent.created_at >= start_date)
        if end_date:
            query = query.where(NormalizedPaymentEvent.created_at <= end_date)

        results = self.session.exec(query).all()

        return [{"provider": provider, "count": count} for provider, count in results]

    def _get_transaction_volume(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Obtiene volumen transaccional en USD"""
        query = select(
            func.sum(NormalizedPaymentEvent.amount_usd_equivalent).label("total"),
            func.avg(NormalizedPaymentEvent.amount_usd_equivalent).label("average"),
            func.count(NormalizedPaymentEvent.id).label("transaction_count"),
        ).where(NormalizedPaymentEvent.amount_usd_equivalent.isnot(None))

        if start_date:
            query = query.where(NormalizedPaymentEvent.created_at >= start_date)
        if end_date:
            query = query.where(NormalizedPaymentEvent.created_at <= end_date)
        if provider:
            query = query.where(NormalizedPaymentEvent.provider == provider.lower())

        result = self.session.exec(query).one()

        return {
            "total_usd": float(result.total) if result.total else 0.0,
            "average_usd": float(result.average) if result.average else 0.0,
            "transaction_count": result.transaction_count,
        }

    def _get_error_source_distribution(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        provider: str | None = None,
    ) -> list[dict[str, Any]]:
        """Obtiene distribución de error sources"""
        query = (
            select(
                NormalizedPaymentEvent.error_source,
                func.count(NormalizedPaymentEvent.id).label("count"),
            )
            .where(NormalizedPaymentEvent.error_source.isnot(None))
            .group_by(NormalizedPaymentEvent.error_source)
            .order_by(func.count(NormalizedPaymentEvent.id).desc())
        )

        if start_date:
            query = query.where(NormalizedPaymentEvent.created_at >= start_date)
        if end_date:
            query = query.where(NormalizedPaymentEvent.created_at <= end_date)
        if provider:
            query = query.where(NormalizedPaymentEvent.provider == provider.lower())

        results = self.session.exec(query).all()

        return [
            {"source": source.value if source else "unknown", "count": count}
            for source, count in results
        ]

    def _get_http_status_distribution(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Obtiene distribución de HTTP status codes"""
        query = (
            select(
                NormalizedPaymentEvent.http_status_code,
                func.count(NormalizedPaymentEvent.id).label("count"),
            )
            .where(NormalizedPaymentEvent.http_status_code.isnot(None))
            .group_by(NormalizedPaymentEvent.http_status_code)
            .order_by(func.count(NormalizedPaymentEvent.id).desc())
        )

        if start_date:
            query = query.where(NormalizedPaymentEvent.created_at >= start_date)
        if end_date:
            query = query.where(NormalizedPaymentEvent.created_at <= end_date)

        results = self.session.exec(query).all()

        return [{"http_code": code, "count": count} for code, count in results]

    def _get_avg_latency(
        self,
        provider: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> float | None:
        """
        Obtiene latency promedio desde metadata (si existe)

        Nota: Esto requiere que el campo metadata contenga timing info
        """
        # Por ahora retornamos None - se puede implementar
        # cuando tengamos metadata con timing
        return None
