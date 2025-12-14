"""
Script de prueba para el sistema de alertas con IA y Slack

Genera eventos de pago simulados para probar:
1. Detección de alertas (provider failure, country drop)
2. Enriquecimiento con IA
3. Envío a Slack

Uso:
    python test_alerts_system.py
"""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlmodel import Session

from app.domain.models.enums import FailureReason, PaymentStatus
from app.domain.models.payment_event import NormalizedPaymentEvent
from app.infraestructure.core.db import engine
from app.services.alert_enrichment_service import AlertEnrichmentService
from app.services.alert_service import AlertDetectionService


def generate_test_data(session: Session) -> None:
    """
    Genera datos de prueba que deberían disparar alertas:

    1. Provider "stripe" con 40% success rate (alerta CRITICAL)
    2. Provider "adyen" con 75% success rate (alerta WARNING)
    3. País "MX" con caída del 30% vs hora anterior
    """
    now = datetime.now(UTC)
    one_hour_ago = now - timedelta(hours=1)
    two_hours_ago = now - timedelta(hours=2)

    print("🔧 Generando datos de prueba...")

    # Período anterior (2-1 horas atrás): México con 90% success
    print("\n📊 Período anterior (bueno):")
    for i in range(100):
        event = NormalizedPaymentEvent(
            id=uuid4(),
            merchant_name="Test Merchant",
            provider="stripe",
            country="MX",
            amount=100.0,
            currency="USD",
            status_category=PaymentStatus.APPROVED if i < 90 else PaymentStatus.FAILED,
            failure_reason=FailureReason.INSUFFICIENT_FUNDS if i >= 90 else None,
            created_at=two_hours_ago + timedelta(minutes=i % 60),
        )
        session.add(event)
    print("  ✅ 100 eventos en MX (90% approved)")

    # Período actual (última hora): Stripe fallando, México con caída
    print("\n⚠️  Período actual (problemas):")

    # Stripe con 40% success (CRITICAL)
    for i in range(100):
        event = NormalizedPaymentEvent(
            id=uuid4(),
            merchant_name="Merchant A" if i < 50 else "Merchant B",
            provider="stripe",
            country="MX" if i < 60 else "US",
            amount=100.0,
            currency="USD",
            status_category=PaymentStatus.APPROVED if i < 40 else PaymentStatus.FAILED,
            failure_reason=(
                FailureReason.INSUFFICIENT_FUNDS if i % 2 == 0 else FailureReason.CARD_DECLINED
            )
            if i >= 40
            else None,
            created_at=one_hour_ago + timedelta(minutes=i % 60),
        )
        session.add(event)
    print("  ⚠️  100 eventos Stripe (40% approved) - CRITICAL")
    print("      • 60 en MX, 40 en US")
    print("      • Merchant A: 50 txs")
    print("      • Merchant B: 50 txs")

    # Adyen con 75% success (WARNING)
    for i in range(100):
        event = NormalizedPaymentEvent(
            id=uuid4(),
            merchant_name="Merchant C",
            provider="adyen",
            country="BR" if i < 50 else "AR",
            amount=100.0,
            currency="USD",
            status_category=PaymentStatus.APPROVED if i < 75 else PaymentStatus.FAILED,
            failure_reason=FailureReason.CARD_DECLINED if i >= 75 else None,
            created_at=one_hour_ago + timedelta(minutes=i % 60),
        )
        session.add(event)
    print("  ⚠️  100 eventos Adyen (75% approved) - WARNING")

    session.commit()
    print("\n✅ Datos de prueba generados")
    print("\n📈 Esperado:")
    print("  • CRITICAL: Provider STRIPE está fallando (40% < 60%)")
    print("  • WARNING: Provider ADYEN está degradado (75% < 80%)")
    print("  • CRITICAL: Caída conversión MX (90% → 67%)")


async def test_alert_detection(session: Session) -> None:
    """Prueba la detección de alertas"""
    print("\n" + "=" * 60)
    print("🔍 DETECTANDO ALERTAS...")
    print("=" * 60)

    service = AlertDetectionService(session)
    alerts = service.detect_all_alerts(time_window_hours=1)

    print(f"\n✅ Se detectaron {len(alerts)} alertas\n")

    for i, alert in enumerate(alerts, 1):
        severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🟢"}
        emoji = severity_emoji.get(alert["severity"], "⚪")

        print(f"{emoji} Alerta #{i}: {alert['severity'].upper()}")
        print(f"   Tipo: {alert['type']}")
        print(f"   Título: {alert['title']}")
        print(f"   Mensaje: {alert['message']}")

        if "provider" in alert:
            print(f"   Provider: {alert['provider']}")
            print(f"   Success rate: {alert['success_rate']}%")

            if "merchants_affected" in alert:
                print(f"   Merchants afectados: {len(alert['merchants_affected'])}")
                for merchant in alert["merchants_affected"][:2]:
                    print(f"      • {merchant['merchant_name']}: {merchant['success_rate']}%")

            if "countries_affected" in alert:
                print(f"   Países afectados: {len(alert['countries_affected'])}")
                for country in alert["countries_affected"][:2]:
                    print(f"      • {country['country']}: {country['success_rate']}%")

        if "country_analysis" in alert:
            print("   Análisis por país:")
            for country in alert["country_analysis"][:3]:
                print(
                    f"      • {country['country']}: {country['previous_success_rate']}% → {country['current_success_rate']}% ({country['drop_percentage']}% drop)"
                )

        print()

    return alerts


async def test_ai_enrichment(alerts: list) -> list:
    """Prueba el enriquecimiento con IA"""
    print("\n" + "=" * 60)
    print("🤖 ENRIQUECIENDO CON IA...")
    print("=" * 60)

    service = AlertEnrichmentService()
    enriched = service.enrich_alerts_batch(alerts, max_alerts=10)

    print(f"\n✅ {len(enriched)} alertas enriquecidas\n")

    for i, alert in enumerate(enriched, 1):
        if "ai_analysis" not in alert:
            print(f"⚪ Alerta #{i}: Sin análisis IA (límite alcanzado)")
            continue

        ai = alert["ai_analysis"]

        print(f"🤖 Alerta #{i}: {alert['title']}")
        print("\n   📝 Explicación:")
        print(f"      {ai.get('explanation', 'N/A')}")
        print(f"\n   🎯 Fuente del error: {ai.get('error_source', 'N/A').upper()}")

        affected = ai.get("affected_parties", {})
        parties = []
        if affected.get("provider"):
            parties.append("Provider")
        if affected.get("merchant"):
            parties.append("Merchant")
        if affected.get("customer"):
            parties.append("Customer")
        print(f"   👥 Partes afectadas: {', '.join(parties) if parties else 'N/A'}")

        print("\n   💰 Impacto:")
        print(f"      {ai.get('impact', 'N/A')}")

        if ai.get("recommended_actions"):
            print("\n   ✅ Acciones recomendadas:")
            for action in ai["recommended_actions"][:3]:
                print(f"      • {action}")

        print("\n   🔍 Causa probable:")
        print(f"      {ai.get('root_cause_hypothesis', 'N/A')}")

        if ai.get("geographic_context"):
            print("\n   🌎 Contexto geográfico:")
            print(f"      {ai['geographic_context']}")

        print(f"\n   ⏰ Urgencia: {ai.get('urgency_level', 'N/A').upper()}")
        print()

    return enriched


async def test_slack_integration(enriched_alerts: list) -> None:
    """Prueba el envío a Slack (solo simula, no envía realmente)"""
    print("\n" + "=" * 60)
    print("💬 INTEGRACIÓN SLACK...")
    print("=" * 60)

    from app.infraestructure.core.config import settings

    if not settings.SLACK_BOT_TOKEN:
        print("\n⚠️  SLACK_BOT_TOKEN no configurado")
        print("   Para probar con Slack real, configura:")
        print("   export SLACK_BOT_TOKEN=xoxb-...")
        print("   export SLACK_ALERTS_CHANNEL=C...")
        print("\n   Simulando envío a Slack...\n")

    critical_alerts = [a for a in enriched_alerts if a.get("severity") == "critical"]

    print(f"📊 Alertas críticas para enviar: {len(critical_alerts)}\n")

    for i, alert in enumerate(critical_alerts, 1):
        print(f"💬 Mensaje Slack #{i}:")
        print("   Canal: #payments-alerts")
        print(f"   Título: 🚨 {alert['title']}")
        print(f"   Provider: {alert.get('provider', 'N/A')}")

        if "ai_analysis" in alert:
            ai = alert["ai_analysis"]
            print("   Análisis IA incluido: ✅")
            print(f"   Fuente error: {ai.get('error_source', 'N/A')}")
            print(f"   Urgencia: {ai.get('urgency_level', 'N/A')}")

        print()

    if settings.SLACK_BOT_TOKEN:
        print("✅ Slack configurado - Las alertas se enviarán automáticamente")
    else:
        print("ℹ️  Para habilitar Slack, configura las variables de entorno")


async def main():
    """Función principal"""
    print("\n" + "=" * 60)
    print("🧪 PRUEBA COMPLETA DEL SISTEMA DE ALERTAS")
    print("=" * 60)

    with Session(engine) as session:
        # 1. Generar datos de prueba
        generate_test_data(session)

        # 2. Detectar alertas
        alerts = await test_alert_detection(session)

        # 3. Enriquecer con IA
        enriched = await test_ai_enrichment(alerts)

        # 4. Simular envío a Slack
        await test_slack_integration(enriched)

    print("\n" + "=" * 60)
    print("✅ PRUEBA COMPLETADA")
    print("=" * 60)
    print("\n📌 Próximos pasos:")
    print("   1. Configurar Slack (SLACK_BOT_TOKEN, SLACK_ALERTS_CHANNEL)")
    print("   2. Probar endpoint: GET /api/alerts/alerts?time_window_hours=1")
    print("   3. Verificar alertas en Slack automáticamente")
    print()


if __name__ == "__main__":
    asyncio.run(main())
