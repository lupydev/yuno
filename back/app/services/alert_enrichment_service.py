"""
Alert AI Enrichment Service

Servicio opcional para enriquecer alertas con IA.
Genera explicaciones human-readable y recomendaciones de acción.
"""

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.infraestructure.ai.langchain_client import LangChainClient

logger = logging.getLogger(__name__)


ALERT_ENRICHMENT_SYSTEM_PROMPT = """You are an expert payment systems analyst specializing in incident response and root cause analysis.

Your task is to analyze payment system alerts and provide:
1. **Clear Explanation**: What's happening in simple terms
2. **Root Cause Analysis**: Identify if the error is from:
   - PROVIDER: Gateway/PSP technical issues (timeout, API errors, maintenance)
   - MERCHANT: Configuration issues (invalid credentials, account limits, permissions)
   - CUSTOMER: User-side issues (insufficient funds, expired card, wrong data)
   - SYSTEM: Our platform issues
3. **Potential Impact**: Business/revenue impact with estimates
4. **Recommended Actions**: Specific steps to resolve immediately
5. **Geographic Analysis**: If it's a country-specific issue, explain why

Be concise, actionable, and prioritize user experience.

Response format (JSON):
{
  "explanation": "Clear explanation of the issue in Spanish",
  "error_source": "provider|merchant|customer|system|multiple",
  "affected_parties": {
    "provider": true/false,
    "merchant": true/false,
    "customer": true/false
  },
  "impact": "Estimated business impact with numbers",
  "recommended_actions": [
    "Immediate action 1",
    "Immediate action 2",
    "Follow-up action"
  ],
  "root_cause_hypothesis": "Most likely root cause with technical details",
  "urgency_level": "immediate|high|medium|low",
  "geographic_context": "If country-specific, explain regulatory/technical reasons"
}
"""


class AlertEnrichmentService:
    """
    Servicio de enriquecimiento de alertas con IA

    OBLIGATORIO: Todas las alertas son enriquecidas con análisis de IA.
    Identifica la fuente del error (provider/merchant/customer) y provee contexto accionable.
    """

    def __init__(self) -> None:
        """Inicializa el servicio de enriquecimiento"""
        self.client = LangChainClient()

    def enrich_alert(
        self,
        alert: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Enriquece una alerta con análisis de IA

        Args:
            alert: Alerta básica del AlertDetectionService
            context: Contexto adicional (opcional)

        Returns:
            Alerta enriquecida con análisis de IA
        """
        try:
            # Preparar contexto para la IA
            alert_context = {
                "alert_type": alert.get("type"),
                "severity": alert.get("severity"),
                "title": alert.get("title"),
                "message": alert.get("message"),
                "metrics": {
                    k: v
                    for k, v in alert.items()
                    if k
                    not in [
                        "type",
                        "severity",
                        "title",
                        "message",
                        "detected_at",
                        "time_window",
                    ]
                },
            }

            if context:
                alert_context["additional_context"] = context

            # Preparar mensajes
            messages = [
                SystemMessage(content=ALERT_ENRICHMENT_SYSTEM_PROMPT),
                HumanMessage(
                    content=f"Analyze this alert and provide insights:\n\n{json.dumps(alert_context, indent=2)}"
                ),
            ]

            # Invocar IA (sin structured output para ser más flexible)
            response = self.client.llm.invoke(messages)

            # Parsear respuesta JSON
            try:
                ai_insights = json.loads(response.content)
            except json.JSONDecodeError:
                # Fallback si no es JSON válido
                ai_insights = {
                    "explanation": response.content,
                    "impact": "Unknown",
                    "recommended_actions": ["Review alert details manually"],
                    "root_cause_hypothesis": "Requires further investigation",
                    "urgency_level": "medium",
                }

            # Combinar alerta original con insights de IA
            enriched_alert = {
                **alert,
                "ai_insights": ai_insights,
                "enriched_at": alert.get("detected_at"),
            }

            logger.info(
                "Alert enriched with AI",
                extra={
                    "alert_type": alert.get("type"),
                    "severity": alert.get("severity"),
                },
            )

            return enriched_alert

        except Exception:
            logger.error(
                "Failed to enrich alert with AI",
                exc_info=True,
                extra={"alert_type": alert.get("type")},
            )

            # Retornar alerta original si falla la IA
            return alert

    def enrich_alerts_batch(
        self,
        alerts: list[dict[str, Any]],
        max_alerts: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Enriquece múltiples alertas (solo las más críticas)

        Args:
            alerts: Lista de alertas
            max_alerts: Máximo de alertas a enriquecer (para controlar costos)

        Returns:
            Alertas enriquecidas
        """
        # Ordenar por severidad (critical primero)
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        sorted_alerts = sorted(
            alerts, key=lambda a: severity_order.get(a.get("severity", "info"), 3)
        )

        # Enriquecer solo las más importantes
        enriched = []
        for i, alert in enumerate(sorted_alerts):
            if i < max_alerts:
                enriched.append(self.enrich_alert(alert))
            else:
                # Resto sin enriquecer
                enriched.append(alert)

        return enriched
