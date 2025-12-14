"""
Test para verificar el enriquecimiento de alertas con IA y generación de formato Slack.

Este script prueba el flujo completo:
1. Detección de alertas
2. Enriquecimiento con IA (análisis + formato Slack)
3. Verificación de que el formato se genera correctamente
"""

import asyncio
import json
import logging
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, create_engine

from app.infraestructure.core.config import settings
from app.infraestructure.core.logging import setup_logging
from app.services.alert_enrichment_service import AlertEnrichmentService
from app.services.alert_service import AlertDetectionService

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)


def test_ai_enrichment_with_slack_format():
    """Prueba el enriquecimiento de IA con formato de Slack"""
    print("\n" + "=" * 80)
    print("🧪 TEST: AI Enrichment con Formato Slack")
    print("=" * 80)

    # Crear una alerta de ejemplo (simulada)
    sample_alert = {
        "type": "provider_failure",
        "severity": "critical",
        "title": "Provider STRIPE está fallando críticamente",
        "message": "Success rate de 45% (< 60%)",
        "provider": "stripe",
        "success_rate": 45.0,
        "total_events": 100,
        "failed_events": 55,
        "detected_at": datetime.now(UTC).isoformat(),
        "time_window": "1 hour",
    }

    print("\n📋 Alerta original:")
    print(json.dumps(sample_alert, indent=2, ensure_ascii=False))

    # Enriquecer con IA
    print("\n🤖 Enriqueciendo con IA...")
    try:
        enrichment_service = AlertEnrichmentService()
        enriched_alert = enrichment_service.enrich_alert(sample_alert)

        print("\n✅ Enriquecimiento completado!")

        # Verificar análisis de IA
        if "ai_analysis" in enriched_alert:
            print("\n📊 Análisis de IA:")
            ai = enriched_alert["ai_analysis"]
            print(f"  - Explicación: {ai.get('explanation', 'N/A')[:100]}...")
            print(f"  - Fuente del error: {ai.get('error_source', 'N/A')}")
            print(f"  - Urgencia: {ai.get('urgency_level', 'N/A')}")
            print(f"  - Impacto: {ai.get('impact', 'N/A')[:80]}...")
            if ai.get("recommended_actions"):
                print(
                    f"  - Acciones recomendadas: {len(ai.get('recommended_actions', []))} items")

        # Verificar formato de Slack generado por IA
        if "ai_slack_blocks" in enriched_alert and enriched_alert["ai_slack_blocks"]:
            print("\n🎨 Formato de Slack generado por IA:")
            blocks = enriched_alert["ai_slack_blocks"]
            print(f"  - Total de bloques: {len(blocks)}")

            for i, block in enumerate(blocks, 1):
                block_type = block.get("type", "unknown")
                print(f"  - Bloque {i}: {block_type}")

                if block_type == "header":
                    text = block.get("text", {}).get("text", "N/A")
                    print(f"    → {text}")
                elif block_type == "section":
                    text = block.get("text", {}).get("text", "N/A")
                    if len(text) > 100:
                        text = text[:100] + "..."
                    print(f"    → {text}")

            # Mostrar color sugerido
            if "ai_suggested_color" in enriched_alert:
                print(
                    f"\n  - Color sugerido: {enriched_alert['ai_suggested_color']}")
            if "ai_suggested_emoji" in enriched_alert:
                print(
                    f"  - Emoji sugerido: {enriched_alert['ai_suggested_emoji']}")

            # Guardar ejemplo completo para inspección
            print("\n💾 Guardando ejemplo completo en 'sample_enriched_alert.json'...")
            with open("sample_enriched_alert.json", "w", encoding="utf-8") as f:
                json.dump(enriched_alert, f, indent=2, ensure_ascii=False)
            print("   Archivo guardado exitosamente!")

        else:
            print("\n⚠️  No se generaron bloques de Slack personalizados")
            print("   (Se usará el formato por defecto)")

        return enriched_alert

    except Exception as e:
        logger.error(f"Error durante el enriquecimiento: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return None


async def test_integration_with_database():
    """Prueba la integración completa con la base de datos"""
    print("\n" + "=" * 80)
    print("🔗 TEST: Integración Completa con Base de Datos")
    print("=" * 80)

    if not settings.database_url:
        print("\n⚠️  Base de datos no configurada")
        print("   Configurar DATABASE_URL para probar con datos reales")
        return

    try:
        # Crear engine y sesión
        engine = create_engine(str(settings.database_url))
        session = Session(engine)

        # Detectar alertas
        print("\n🔍 Detectando alertas automáticas...")
        alert_service = AlertDetectionService(session)
        alerts = alert_service.detect_all_alerts(time_window_hours=1)

        print(f"   Alertas detectadas: {len(alerts)}")

        if len(alerts) > 0:
            # Enriquecer con IA
            print("\n🤖 Enriqueciendo alertas con IA...")
            enrichment_service = AlertEnrichmentService()
            enriched_alerts = enrichment_service.enrich_alerts_batch(
                alerts, max_alerts=3)

            print(f"   Alertas enriquecidas: {len(enriched_alerts)}")

            # Verificar formato de Slack
            with_ai_blocks = [
                a for a in enriched_alerts if a.get("ai_slack_blocks")]
            print(f"   Alertas con formato Slack de IA: {len(with_ai_blocks)}")

            if with_ai_blocks:
                print("\n✅ Formato de Slack generado exitosamente!")
                print(f"   Ejemplo: {with_ai_blocks[0].get('title', 'N/A')}")
                print(
                    f"   Bloques: {len(with_ai_blocks[0].get('ai_slack_blocks', []))}")
            else:
                print("\n⚠️  No se generaron formatos personalizados de Slack")

        else:
            print("\n   No hay alertas en este momento para probar")

        session.close()

    except Exception as e:
        logger.error(f"Error en integración: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")


def main():
    """Función principal"""
    print("\n" + "=" * 80)
    print("🚀 PRUEBA DE NOTIFICACIONES CON IA")
    print("=" * 80)
    print("\nEste script prueba:")
    print("  1. Enriquecimiento de alertas con IA")
    print("  2. Generación de formato Slack personalizado")
    print("  3. Integración completa del flujo")

    # Test 1: Enriquecimiento básico
    enriched = test_ai_enrichment_with_slack_format()

    # Test 2: Integración con BD (si está disponible)
    if enriched and enriched.get("ai_slack_blocks"):
        print("\n✅ Test básico exitoso!")
        print("\nPara probar con datos reales, ejecutar:")
        print("  asyncio.run(test_integration_with_database())")
    else:
        print("\n⚠️  Test completado con warnings")

    print("\n" + "=" * 80)
    print("Prueba finalizada")
    print("=" * 80)


if __name__ == "__main__":
    main()
