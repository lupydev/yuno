"""
Alert Detection Service

Servicio para detectar alertas automáticas basadas en métricas de pagos.
Usa reglas determinísticas para velocidad y confiabilidad.
"""

import logging
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from sqlmodel import Session

from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Severidad de la alerta"""

    CRITICAL = "critical"  # Requiere acción inmediata
    WARNING = "warning"  # Requiere atención
    INFO = "info"  # Informativo


class AlertType(str, Enum):
    """Tipo de alerta"""

    PROVIDER_FAILURE = "provider_failure"  # Provider con alta tasa de fallo
    COUNTRY_CONVERSION_DROP = "country_conversion_drop"  # Caída de conversión en país
    HIGH_ERROR_RATE = "high_error_rate"  # Tasa de error alta general
    ERROR_SPIKE = "error_spike"  # Spike en errores específicos
    PROVIDER_DEGRADED = "provider_degraded"  # Provider degradado pero no crítico


class AlertDetectionService:
    """
    Servicio de detección de alertas

    Detecta anomalías y problemas en tiempo real usando:
    - Reglas determinísticas (umbrales configurables)
    - Análisis de tendencias (comparación con períodos anteriores)
    - Análisis por dimensión (provider, país, error)
    """

    # Umbrales configurables
    CRITICAL_SUCCESS_RATE = 60.0  # < 60% es crítico
    WARNING_SUCCESS_RATE = 80.0  # < 80% es warning
    CRITICAL_ERROR_COUNT = 50  # > 50 errores en ventana es crítico
    WARNING_ERROR_COUNT = 20  # > 20 errores es warning
    CONVERSION_DROP_THRESHOLD = 20.0  # > 20% drop es crítico

    def __init__(self, session: Session) -> None:
        """
        Inicializa el servicio de alertas

        Args:
            session: SQLModel Session (sync)
        """
        self.session = session
        self.analytics = AnalyticsService(session)

    def detect_all_alerts(
        self,
        time_window_hours: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Detecta todas las alertas para el período especificado

        Args:
            time_window_hours: Ventana de tiempo en horas (default: 1h)

        Returns:
            Lista de alertas detectadas
        """
        now = datetime.now(UTC)
        start_time = now - timedelta(hours=time_window_hours)

        alerts = []

        # 1. Alertas por provider
        provider_alerts = self._detect_provider_alerts(start_time, now)
        alerts.extend(provider_alerts)

        # 2. Alertas por país
        country_alerts = self._detect_country_alerts(start_time, now)
        alerts.extend(country_alerts)

        # 3. Alertas por tipo de error
        error_alerts = self._detect_error_alerts(start_time, now)
        alerts.extend(error_alerts)

        # 4. Alerta general de sistema
        system_alerts = self._detect_system_alerts(start_time, now)
        alerts.extend(system_alerts)

        logger.info(
            "Alert detection completed",
            extra={
                "time_window_hours": time_window_hours,
                "total_alerts": len(alerts),
                "critical": len([a for a in alerts if a["severity"] == AlertSeverity.CRITICAL]),
                "warning": len([a for a in alerts if a["severity"] == AlertSeverity.WARNING]),
                "info": len([a for a in alerts if a["severity"] == AlertSeverity.INFO]),
            },
        )

        return alerts

    def _detect_provider_alerts(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """Detecta alertas relacionadas con providers"""
        alerts = []

        # Obtener providers activos en el período
        provider_dist = self.analytics._get_provider_distribution(start_time, end_time)

        for provider_info in provider_dist:
            provider = provider_info["provider"]

            # Obtener stats del provider
            stats = self.analytics.get_provider_stats(provider, start_time, end_time)

            if stats["total_events"] == 0:
                continue

            success_rate = stats["success_rate"]

            # Alerta crítica: Success rate muy bajo
            if success_rate < self.CRITICAL_SUCCESS_RATE:
                # Obtener merchants afectados
                merchants_affected = self._get_affected_merchants(
                    provider, start_time, end_time, max_merchants=5
                )

                # Obtener países afectados
                countries_affected = self._get_affected_countries(
                    provider, start_time, end_time, max_countries=5
                )

                alerts.append(
                    {
                        "severity": AlertSeverity.CRITICAL,
                        "type": AlertType.PROVIDER_FAILURE,
                        "title": f"Provider {provider.upper()} está fallando críticamente",
                        "message": f"Success rate de {success_rate}% (< {self.CRITICAL_SUCCESS_RATE}%). "
                        f"{len(merchants_affected)} merchants afectados en {len(countries_affected)} países",
                        "provider": provider,
                        "success_rate": success_rate,
                        "total_events": stats["total_events"],
                        "failed_events": stats["total_events"]
                        - int(stats["total_events"] * success_rate / 100),
                        "top_failures": stats["failure_reasons"][:3],
                        "merchants_affected": merchants_affected,
                        "countries_affected": countries_affected,
                        "detected_at": datetime.now(UTC).isoformat(),
                        "time_window": {
                            "start": start_time.isoformat(),
                            "end": end_time.isoformat(),
                        },
                    }
                )

            # Alerta warning: Success rate degradado
            elif success_rate < self.WARNING_SUCCESS_RATE:
                # Obtener merchants afectados
                merchants_affected = self._get_affected_merchants(
                    provider, start_time, end_time, max_merchants=3
                )

                alerts.append(
                    {
                        "severity": AlertSeverity.WARNING,
                        "type": AlertType.PROVIDER_DEGRADED,
                        "title": f"Provider {provider.upper()} está degradado",
                        "message": f"Success rate de {success_rate}% (< {self.WARNING_SUCCESS_RATE}%). "
                        f"{len(merchants_affected)} merchants afectados",
                        "provider": provider,
                        "success_rate": success_rate,
                        "total_events": stats["total_events"],
                        "top_failures": stats["failure_reasons"][:3],
                        "merchants_affected": merchants_affected,
                        "detected_at": datetime.now(UTC).isoformat(),
                        "time_window": {
                            "start": start_time.isoformat(),
                            "end": end_time.isoformat(),
                        },
                    }
                )

        return alerts

    def _detect_country_alerts(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """Detecta alertas relacionadas con conversión por país"""
        alerts = []

        # Período anterior (mismo tamaño de ventana)
        window_size = end_time - start_time
        previous_start = start_time - window_size
        previous_end = start_time

        # Obtener métricas actuales
        current_metrics = self.analytics.get_metrics_summary(start_time, end_time)

        # Obtener métricas anteriores
        previous_metrics = self.analytics.get_metrics_summary(previous_start, previous_end)

        # Comparar success rate
        current_rate = current_metrics["success_rate"]
        previous_rate = previous_metrics["success_rate"]

        if previous_rate > 0:
            drop_percentage = ((previous_rate - current_rate) / previous_rate) * 100

            # Alerta crítica: Caída significativa en conversión
            if drop_percentage > self.CONVERSION_DROP_THRESHOLD:
                # Analizar por país para identificar cuál bajó
                country_analysis = self._analyze_country_conversion_drop(
                    start_time, end_time, previous_start, previous_end
                )

                alerts.append(
                    {
                        "severity": AlertSeverity.CRITICAL,
                        "type": AlertType.COUNTRY_CONVERSION_DROP,
                        "title": "Caída significativa en conversión global",
                        "message": f"Success rate bajó {drop_percentage:.1f}% ({previous_rate:.1f}% → {current_rate:.1f}%). "
                        f"Países más afectados: {', '.join([c['country'] for c in country_analysis[:3]])}",
                        "current_success_rate": current_rate,
                        "previous_success_rate": previous_rate,
                        "drop_percentage": drop_percentage,
                        "country_analysis": country_analysis,
                        "detected_at": datetime.now(UTC).isoformat(),
                        "time_window": {
                            "current": {
                                "start": start_time.isoformat(),
                                "end": end_time.isoformat(),
                            },
                            "previous": {
                                "start": previous_start.isoformat(),
                                "end": previous_end.isoformat(),
                            },
                        },
                    }
                )

        return alerts

    def _detect_error_alerts(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """Detecta alertas relacionadas con errores específicos"""
        alerts = []

        # Obtener análisis de fallos
        failure_analysis = self.analytics.get_failure_analysis(start_time, end_time, limit=10)

        top_failures = failure_analysis["top_failure_reasons"]

        if len(top_failures) > 0:
            # Error más impactante
            most_impactful = top_failures[0]

            # Alerta crítica: Muchos errores de un tipo
            if most_impactful["count"] > self.CRITICAL_ERROR_COUNT:
                alerts.append(
                    {
                        "severity": AlertSeverity.CRITICAL,
                        "type": AlertType.ERROR_SPIKE,
                        "title": f"Spike crítico de errores: {most_impactful['reason']}",
                        "message": f"{most_impactful['count']} ocurrencias detectadas",
                        "error_reason": most_impactful["reason"],
                        "error_count": most_impactful["count"],
                        "error_sources": failure_analysis["error_source_distribution"],
                        "detected_at": datetime.now(UTC).isoformat(),
                        "time_window": {
                            "start": start_time.isoformat(),
                            "end": end_time.isoformat(),
                        },
                    }
                )

            # Alerta warning: Errores moderados
            elif most_impactful["count"] > self.WARNING_ERROR_COUNT:
                alerts.append(
                    {
                        "severity": AlertSeverity.WARNING,
                        "type": AlertType.ERROR_SPIKE,
                        "title": f"Errores frecuentes: {most_impactful['reason']}",
                        "message": f"{most_impactful['count']} ocurrencias detectadas",
                        "error_reason": most_impactful["reason"],
                        "error_count": most_impactful["count"],
                        "detected_at": datetime.now(UTC).isoformat(),
                        "time_window": {
                            "start": start_time.isoformat(),
                            "end": end_time.isoformat(),
                        },
                    }
                )

        return alerts

    def _detect_system_alerts(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> list[dict[str, Any]]:
        """Detecta alertas de sistema general"""
        alerts = []

        # Obtener métricas generales
        metrics = self.analytics.get_metrics_summary(start_time, end_time)

        # Alerta info: Sistema saludable
        if metrics["success_rate"] >= 95.0:
            alerts.append(
                {
                    "severity": AlertSeverity.INFO,
                    "type": AlertType.HIGH_ERROR_RATE,
                    "title": "Sistema operando normalmente",
                    "message": f"Success rate: {metrics['success_rate']}%",
                    "success_rate": metrics["success_rate"],
                    "total_events": metrics["total_events"],
                    "detected_at": datetime.now(UTC).isoformat(),
                }
            )

        return alerts

    def get_alert_summary(
        self,
        time_window_hours: int = 1,
    ) -> dict[str, Any]:
        """
        Obtiene resumen de alertas con conteo por severidad

        Args:
            time_window_hours: Ventana de tiempo

        Returns:
            Resumen de alertas
        """
        alerts = self.detect_all_alerts(time_window_hours)

        return {
            "total_alerts": len(alerts),
            "by_severity": {
                "critical": len([a for a in alerts if a["severity"] == AlertSeverity.CRITICAL]),
                "warning": len([a for a in alerts if a["severity"] == AlertSeverity.WARNING]),
                "info": len([a for a in alerts if a["severity"] == AlertSeverity.INFO]),
            },
            "by_type": {
                alert_type: len([a for a in alerts if a["type"] == alert_type])
                for alert_type in AlertType
            },
            "alerts": alerts,
            "generated_at": datetime.now(UTC).isoformat(),
            "time_window_hours": time_window_hours,
        }

    def _get_affected_merchants(
        self,
        provider: str,
        start_time: datetime,
        end_time: datetime,
        max_merchants: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Obtiene merchants afectados por un provider con problemas

        Returns:
            Lista de merchants con sus métricas
        """
        from sqlmodel import case, func, select

        from app.domain.models.enums import PaymentStatus
        from app.domain.models.payment_event import NormalizedPaymentEvent

        # Query para obtener merchants del provider con stats
        query = (
            select(
                NormalizedPaymentEvent.merchant_name,
                func.count().label("total"),
                func.sum(
                    case(
                        (NormalizedPaymentEvent.status_category == PaymentStatus.APPROVED, 1),
                        else_=0,
                    )
                ).label("approved"),
            )
            .where(NormalizedPaymentEvent.provider == provider)
            .where(NormalizedPaymentEvent.created_at >= start_time)
            .where(NormalizedPaymentEvent.created_at <= end_time)
            .group_by(NormalizedPaymentEvent.merchant_name)
            .order_by(func.count().desc())
            .limit(max_merchants)
        )

        results = self.session.exec(query).all()

        merchants = []
        for row in results:
            total = row.total
            approved = row.approved or 0
            success_rate = (approved / total * 100) if total > 0 else 0

            merchants.append(
                {
                    "merchant_name": row.merchant_name,
                    "total_events": total,
                    "success_rate": round(success_rate, 2),
                    "failed_events": total - approved,
                }
            )

        return merchants

    def _get_affected_countries(
        self,
        provider: str,
        start_time: datetime,
        end_time: datetime,
        max_countries: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Obtiene países afectados por un provider con problemas

        Returns:
            Lista de países con sus métricas
        """
        from sqlmodel import case, func, select

        from app.domain.models.enums import PaymentStatus
        from app.domain.models.payment_event import NormalizedPaymentEvent

        # Query para obtener países del provider con stats
        query = (
            select(
                NormalizedPaymentEvent.country,
                func.count().label("total"),
                func.sum(
                    case(
                        (NormalizedPaymentEvent.status_category == PaymentStatus.APPROVED, 1),
                        else_=0,
                    )
                ).label("approved"),
            )
            .where(NormalizedPaymentEvent.provider == provider)
            .where(NormalizedPaymentEvent.country.is_not(None))
            .where(NormalizedPaymentEvent.created_at >= start_time)
            .where(NormalizedPaymentEvent.created_at <= end_time)
            .group_by(NormalizedPaymentEvent.country)
            .order_by(func.count().desc())
            .limit(max_countries)
        )

        results = self.session.exec(query).all()

        countries = []
        for row in results:
            total = row.total
            approved = row.approved or 0
            success_rate = (approved / total * 100) if total > 0 else 0

            countries.append(
                {
                    "country": row.country,
                    "total_events": total,
                    "success_rate": round(success_rate, 2),
                    "failed_events": total - approved,
                }
            )

        return countries

    def _analyze_country_conversion_drop(
        self,
        current_start: datetime,
        current_end: datetime,
        previous_start: datetime,
        previous_end: datetime,
    ) -> list[dict[str, Any]]:
        """
        Analiza qué países tuvieron caída de conversión

        Returns:
            Lista de países ordenados por magnitud de caída
        """
        from sqlmodel import case, func, select

        from app.domain.models.enums import PaymentStatus
        from app.domain.models.payment_event import NormalizedPaymentEvent

        # Obtener stats por país en período actual
        current_query = (
            select(
                NormalizedPaymentEvent.country,
                func.count().label("total"),
                func.sum(
                    case(
                        (NormalizedPaymentEvent.status_category == PaymentStatus.APPROVED, 1),
                        else_=0,
                    )
                ).label("approved"),
            )
            .where(NormalizedPaymentEvent.country.is_not(None))
            .where(NormalizedPaymentEvent.created_at >= current_start)
            .where(NormalizedPaymentEvent.created_at <= current_end)
            .group_by(NormalizedPaymentEvent.country)
        )

        current_results = self.session.exec(current_query).all()
        current_by_country = {
            row.country: {
                "total": row.total,
                "approved": row.approved or 0,
                "success_rate": ((row.approved or 0) / row.total * 100) if row.total > 0 else 0,
            }
            for row in current_results
        }

        # Obtener stats por país en período anterior
        previous_query = (
            select(
                NormalizedPaymentEvent.country,
                func.count().label("total"),
                func.sum(
                    case(
                        (NormalizedPaymentEvent.status_category == PaymentStatus.APPROVED, 1),
                        else_=0,
                    )
                ).label("approved"),
            )
            .where(NormalizedPaymentEvent.country.is_not(None))
            .where(NormalizedPaymentEvent.created_at >= previous_start)
            .where(NormalizedPaymentEvent.created_at <= previous_end)
            .group_by(NormalizedPaymentEvent.country)
        )

        previous_results = self.session.exec(previous_query).all()
        previous_by_country = {
            row.country: {
                "total": row.total,
                "approved": row.approved or 0,
                "success_rate": ((row.approved or 0) / row.total * 100) if row.total > 0 else 0,
            }
            for row in previous_results
        }

        # Comparar y calcular caídas
        countries_with_drop = []
        for country in current_by_country:
            if country in previous_by_country:
                current_rate = current_by_country[country]["success_rate"]
                previous_rate = previous_by_country[country]["success_rate"]

                if previous_rate > 0:
                    drop = previous_rate - current_rate
                    drop_percentage = (drop / previous_rate) * 100

                    if drop_percentage > 5.0:  # Solo si cayó más de 5%
                        countries_with_drop.append(
                            {
                                "country": country,
                                "current_success_rate": round(current_rate, 2),
                                "previous_success_rate": round(previous_rate, 2),
                                "drop_percentage": round(drop_percentage, 2),
                                "current_volume": current_by_country[country]["total"],
                            }
                        )

        # Ordenar por magnitud de caída
        countries_with_drop.sort(key=lambda x: x["drop_percentage"], reverse=True)

        return countries_with_drop
