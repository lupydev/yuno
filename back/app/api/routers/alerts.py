"""
Alerts Router

Endpoints para sistema de alertas automáticas con integración a Slack.
"""

import logging
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.domain.models.alert import AlertModel
from app.domain.models.alert import AlertSeverity as DomainAlertSeverity
from app.infraestructure.core.config import settings
from app.infraestructure.core.db import get_session
from app.infraestructure.slack import SlackConfig, SlackNotifierAdapter
from app.services.alert_enrichment_service import AlertEnrichmentService
from app.services.alert_service import AlertDetectionService

logger = logging.getLogger(__name__)

router = APIRouter()

SessionDep = Annotated[Session, Depends(get_session)]


def get_alert_service(session: SessionDep) -> AlertDetectionService:
    """Dependency para inyectar AlertDetectionService"""
    return AlertDetectionService(session)


AlertServiceDep = Annotated[AlertDetectionService, Depends(get_alert_service)]


async def _send_critical_alerts_to_slack(alerts: list[dict[str, Any]]) -> None:
    """
    Envía alertas críticas a Slack con formato enriquecido

    Args:
        alerts: Lista de alertas enriquecidas con IA
    """
    if not settings.SLACK_BOT_TOKEN or not settings.SLACK_ALERTS_CHANNEL:
        logger.warning("Slack not configured, skipping alert notifications")
        return

    config = SlackConfig(
        bot_token=settings.SLACK_BOT_TOKEN,
        signing_secret=settings.SLACK_SIGNING_SECRET,
        default_channel=settings.SLACK_ALERTS_CHANNEL,
        timeout=30,
    )

    async with SlackNotifierAdapter(config=config) as notifier:
        for alert in alerts:
            try:
                # Mapear severidad
                severity_map = {
                    "critical": DomainAlertSeverity.CRITICAL,
                    "warning": DomainAlertSeverity.HIGH,
                    "info": DomainAlertSeverity.INFO,
                }

                # Construir metadata con análisis de IA
                metadata = {
                    "type": alert.get("type", "unknown"),
                    "provider": alert.get("provider", "N/A"),
                    "country": alert.get("country", "N/A"),
                    "success_rate": str(alert.get("success_rate", "N/A")),
                    "total_events": str(alert.get("total_events", 0)),
                }

                # Agregar análisis de IA si existe
                if "ai_analysis" in alert:
                    ai = alert["ai_analysis"]
                    metadata["error_source"] = ai.get("error_source", "unknown")
                    metadata["urgency"] = ai.get("urgency_level", "medium")

                    # Agregar partes afectadas
                    affected = ai.get("affected_parties", {})
                    affected_list = []
                    if affected.get("provider"):
                        affected_list.append("Provider")
                    if affected.get("merchant"):
                        affected_list.append("Merchant")
                    if affected.get("customer"):
                        affected_list.append("Customer")
                    metadata["affected_parties"] = (
                        ", ".join(affected_list) if affected_list else "Unknown"
                    )

                # Construir mensaje con explicación de IA
                message = alert.get("message", "")
                if "ai_analysis" in alert:
                    ai = alert["ai_analysis"]
                    message += f"\n\n🤖 **Análisis IA**:\n{ai.get('explanation', '')}"
                    message += f"\n\n📊 **Impacto**: {ai.get('impact', 'Estimando...')}"

                    if ai.get("recommended_actions"):
                        message += "\n\n✅ **Acciones recomendadas**:"
                        for action in ai.get("recommended_actions", [])[:3]:
                            message += f"\n• {action}"

                    message += f"\n\n🔍 **Causa probable**: {ai.get('root_cause_hypothesis', 'Investigando...')}"

                    if ai.get("geographic_context"):
                        message += f"\n\n🌎 **Contexto geográfico**: {ai['geographic_context']}"

                # Crear modelo de alerta
                alert_model = AlertModel(
                    id=uuid4(),
                    title=alert.get("title", "Alert"),
                    message=message[:3900],  # Slack limit
                    severity=severity_map.get(
                        alert.get("severity", "info"), DomainAlertSeverity.INFO
                    ),
                    source="payment-analytics-ai",
                    metadata=metadata,
                )

                # Enviar a Slack
                message_id = await notifier.send_alert(alert_model)
                logger.info(
                    "Alert sent to Slack",
                    extra={
                        "alert_type": alert.get("type"),
                        "message_ts": message_id.timestamp,
                    },
                )

            except Exception as e:
                logger.error(f"Failed to send individual alert to Slack: {e}", exc_info=True)
                continue


@router.get("/alerts")
async def get_alerts(
    service: AlertServiceDep,
    time_window_hours: int = Query(1, ge=1, le=24, description="Ventana de tiempo en horas"),
    severity: str | None = Query(
        None, description="Filtrar por severidad (critical, warning, info)"
    ),
    send_to_slack: bool = Query(
        True, description="Enviar alertas críticas a Slack automáticamente"
    ),
) -> dict[str, Any]:
    """
    Obtiene alertas detectadas automáticamente con enriquecimiento IA

    TODAS las alertas son enriquecidas con IA para identificar:
    - Si el error es del provider, merchant o customer
    - Análisis de impacto con números
    - Recomendaciones accionables inmediatas
    - Contexto geográfico (si aplica)

    Las alertas críticas se envían automáticamente a Slack.

    Args:
        time_window_hours: Ventana de análisis (1-24h)
        severity: Filtrar por severidad
        send_to_slack: Enviar a Slack (default: true)

    Returns:
        Lista de alertas enriquecidas con IA

    Ejemplo:
    ```
    GET /alerts/alerts?time_window_hours=1
    GET /alerts/alerts?severity=critical
    GET /alerts/alerts?send_to_slack=false
    ```

    Response:
    ```json
    {
      "total_alerts": 3,
      "by_severity": {
        "critical": 1,
        "warning": 2,
        "info": 0
      },
      "alerts": [
        {
          "severity": "critical",
          "type": "provider_failure",
          "title": "Provider STRIPE está fallando críticamente",
          "message": "Success rate de 45% (< 60%)",
          "provider": "stripe",
          "success_rate": 45.0,
          "total_events": 100,
          "failed_events": 55,
          "top_failures": [...]
        }
      ]
    }
    ```
    """
    logger.info(
        "Fetching alerts with AI enrichment",
        extra={
            "time_window_hours": time_window_hours,
            "severity_filter": severity,
            "send_to_slack": send_to_slack,
        },
    )

    # Detectar alertas
    alerts = service.detect_all_alerts(time_window_hours)

    # Filtrar por severidad si se especifica
    if severity:
        alerts = [a for a in alerts if a["severity"] == severity]

    # SIEMPRE enriquecer con IA (obligatorio)
    enriched_alerts = []
    if len(alerts) > 0:
        try:
            enrichment_service = AlertEnrichmentService()
            enriched_alerts = enrichment_service.enrich_alerts_batch(alerts, max_alerts=10)
            logger.info(f"Successfully enriched {len(enriched_alerts)} alerts with AI")
        except Exception as e:
            logger.error(f"Failed to enrich alerts with AI: {e}", exc_info=True)
            # Si falla, usar alertas sin enriquecer
            enriched_alerts = alerts

    # Enviar alertas críticas a Slack automáticamente
    if send_to_slack:
        critical_alerts = [a for a in enriched_alerts if a.get("severity") == "critical"]
        if critical_alerts:
            try:
                await _send_critical_alerts_to_slack(critical_alerts)
                logger.info(f"Sent {len(critical_alerts)} critical alerts to Slack")
            except Exception as e:
                logger.error(f"Failed to send alerts to Slack: {e}", exc_info=True)

    # Calcular estadísticas
    by_severity = {
        "critical": len([a for a in enriched_alerts if a["severity"] == "critical"]),
        "warning": len([a for a in enriched_alerts if a["severity"] == "warning"]),
        "info": len([a for a in enriched_alerts if a["severity"] == "info"]),
    }

    return {
        "total_alerts": len(enriched_alerts),
        "by_severity": by_severity,
        "time_window_hours": time_window_hours,
        "alerts": enriched_alerts,
    }


@router.get("/alerts/summary")
def get_alerts_summary(
    service: AlertServiceDep,
    time_window_hours: int = Query(1, ge=1, le=24, description="Ventana de tiempo en horas"),
) -> dict[str, Any]:
    """
    Obtiene resumen ejecutivo de alertas

    Endpoint ligero para dashboards.
    Solo conteos, sin detalles completos.

    Args:
        time_window_hours: Ventana de análisis (1-24h)

    Returns:
        Resumen de alertas con conteos

    Ejemplo:
    ```
    GET /alerts/alerts/summary
    ```

    Response:
    ```json
    {
      "total_alerts": 5,
      "by_severity": {
        "critical": 1,
        "warning": 3,
        "info": 1
      },
      "by_type": {
        "provider_failure": 1,
        "error_spike": 2,
        "country_conversion_drop": 1
      }
    }
    ```
    """
    summary = service.get_alert_summary(time_window_hours)

    logger.info(
        "Alert summary generated",
        extra={
            "total_alerts": summary["total_alerts"],
            "critical": summary["by_severity"]["critical"],
        },
    )

    return summary


@router.get("/alerts/top-issues")
def get_top_issues(
    service: AlertServiceDep,
    time_window_hours: int = Query(1, ge=1, le=24, description="Ventana de tiempo en horas"),
    limit: int = Query(3, ge=1, le=10, description="Número de issues a retornar"),
) -> dict[str, Any]:
    """
    Obtiene los problemas más críticos

    Responde directamente:
    - ¿Qué error impacta más?
    - ¿Qué provider está fallando?
    - ¿Qué país bajó conversión?

    Args:
        time_window_hours: Ventana de análisis
        limit: Máximo de issues

    Returns:
        Top issues ordenados por impacto

    Ejemplo:
    ```
    GET /alerts/alerts/top-issues?limit=3
    ```
    """
    # Detectar todas las alertas
    all_alerts = service.detect_all_alerts(time_window_hours)

    # Filtrar solo critical y warning
    important_alerts = [a for a in all_alerts if a["severity"] in ["critical", "warning"]]

    # Ordenar por severidad (critical primero)
    severity_order = {"critical": 0, "warning": 1}
    sorted_alerts = sorted(
        important_alerts,
        key=lambda a: severity_order.get(a.get("severity", "warning"), 2),
    )

    # Tomar top N
    top_issues = sorted_alerts[:limit]

    return {
        "total_issues": len(important_alerts),
        "showing": len(top_issues),
        "top_issues": top_issues,
        "questions_answered": {
            "what_error_impacts_most": (
                top_issues[0].get("error_reason")
                if len(top_issues) > 0 and top_issues[0].get("type") == "error_spike"
                else None
            ),
            "which_provider_is_failing": (
                top_issues[0].get("provider")
                if len(top_issues) > 0 and "provider" in top_issues[0].get("type", "")
                else None
            ),
            "conversion_drop_detected": any(
                a.get("type") == "country_conversion_drop" for a in top_issues
            ),
        },
    }
