"""
Script para generar reportes/alertas automáticos usando IA

Este script:
1. Lee eventos de pago normalizados (especialmente los fallidos)
2. Usa OpenAI para generar explicaciones y recomendaciones
3. Inserta los reportes en la base de datos
"""

from app.models.alert_report import AlertReport
from app.domain.models.payment_event import NormalizedPaymentEvent
import os
import random
from datetime import UTC, datetime
from uuid import uuid4

from openai import OpenAI
from sqlalchemy import create_engine, select
from sqlmodel import Session, SQLModel

# Importar desde el proyecto principal
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "back"))


# --- CONFIGURATION ---
DB_DSN = "postgresql://postgres:OymPLdKHtAnAcRyRpjQyPhpCqHMjpsgv@maglev.proxy.rlwy.net:33322/railway"
OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)  # Asegúrate de tener esto en tu .env o exportado

# Número de reportes a generar (se tomarán eventos aleatorios)
NUM_REPORTS = 50


def generate_ai_analysis(event: NormalizedPaymentEvent) -> tuple[str, str]:
    """
    Genera análisis usando OpenAI sobre por qué ocurrió un problema de pago

    Returns:
        tuple: (explicación, recomendación)
    """
    # Si no hay API key, usar fallback directamente
    if not OPENAI_API_KEY:
        return generate_fallback_analysis(event)

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Construir contexto del evento
    context = f"""
Evento de Pago:
- Merchant: {event.merchant_name}
- Proveedor: {event.provider}
- País: {event.country}
- Estado: {event.status_category}
- Razón de fallo: {event.failure_reason or 'N/A'}
- Monto: {event.amount} {event.currency}
- Estado del proveedor: {event.provider_status or 'N/A'}
- Latencia: {event.latency_ms}ms
"""

    # Prompt para explicación
    explanation_prompt = f"""Eres un experto en pagos digitales y sistemas de procesamiento de pagos. 

Analiza el siguiente evento de pago y explica en 2-3 oraciones por qué ocurrió este problema. 
Sé conciso, técnico pero claro.

{context}

Explicación:"""

    # Prompt para recomendación
    recommendation_prompt = f"""Basándote en este evento de pago, proporciona una recomendación práctica y específica en 2-3 oraciones sobre cómo resolver o prevenir este problema.

{context}

Recomendación:"""

    try:
        # Generar explicación
        explanation_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto en sistemas de pagos digitales.",
                },
                {"role": "user", "content": explanation_prompt},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        explanation = explanation_response.choices[0].message.content.strip()

        # Generar recomendación
        recommendation_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto en solucionar problemas de pagos digitales.",
                },
                {"role": "user", "content": recommendation_prompt},
            ],
            max_tokens=200,
            temperature=0.7,
        )
        recommendation = recommendation_response.choices[0].message.content.strip(
        )

        return explanation, recommendation

    except Exception as e:
        print(f"⚠️  Error al generar análisis con IA: {e}")
        # Fallback a mensajes genéricos
        return generate_fallback_analysis(event)


def generate_fallback_analysis(event: NormalizedPaymentEvent) -> tuple[str, str]:
    """Genera análisis fallback sin IA para cuando OpenAI falla"""

    explanations = {
        "insufficient_funds": "El pago fue rechazado porque la cuenta del cliente no tiene fondos suficientes para completar la transacción. Esto es común en tarjetas de débito o cuentas bancarias con saldo bajo.",
        "card_declined": "La tarjeta fue declinada por el banco emisor. Esto puede deberse a múltiples razones como límites de gasto excedidos, tarjeta bloqueada por seguridad, o problemas de autenticación.",
        "expired_card": "La tarjeta de crédito o débito utilizada ya expiró. El cliente necesita actualizar su método de pago con una tarjeta válida.",
        "fraud_suspected": "El sistema antifraude detectó patrones sospechosos en esta transacción. Esto puede incluir comportamiento inusual, ubicación no habitual, o múltiples intentos fallidos.",
        "timeout": f"La transacción excedió el tiempo máximo de espera ({event.latency_ms}ms). Esto generalmente indica problemas de conectividad entre el gateway de pago y el banco procesador.",
        "provider_error": "El proveedor de pagos experimentó un error técnico interno que impidió procesar la transacción. Esto puede ser temporal.",
    }

    recommendations = {
        "insufficient_funds": "Recomendación: Implementar un sistema de notificaciones que alerte al cliente sobre fondos insuficientes antes de intentar el pago. Considerar ofrecer métodos de pago alternativos.",
        "card_declined": "Recomendación: Proporcionar al cliente información detallada sobre por qué fue rechazado y sugerir contactar a su banco. Ofrecer intentar con otro método de pago.",
        "expired_card": "Recomendación: Implementar verificaciones proactivas de fechas de expiración y enviar recordatorios automáticos a los clientes antes de que expiren sus tarjetas.",
        "fraud_suspected": "Recomendación: Implementar autenticación adicional (3DS 2.0) para transacciones de alto riesgo. Revisar y ajustar las reglas del sistema antifraude para reducir falsos positivos.",
        "timeout": "Recomendación: Aumentar el timeout de las transacciones, implementar reintentos automáticos con backoff exponencial, y considerar usar un proveedor de pagos con mejor infraestructura.",
        "provider_error": "Recomendación: Monitorear la disponibilidad del proveedor de pagos y considerar implementar un sistema de failover con proveedores alternativos para mayor redundancia.",
    }

    failure_reason = event.failure_reason or "unknown"
    explanation = explanations.get(
        failure_reason,
        f"La transacción falló con estado '{event.status_category}'. Se necesita revisar los logs del proveedor {event.provider} para obtener más detalles sobre el error específico.",
    )

    recommendation = recommendations.get(
        failure_reason,
        "Recomendación: Revisar los logs detallados del evento, contactar al proveedor de pagos para obtener más información, y considerar implementar mejor manejo de errores y reintentos automáticos.",
    )

    return explanation, recommendation


def main():
    """Función principal para generar reportes"""
    print("=" * 80)
    print("🚨 Generador de Reportes/Alertas Automáticos con IA")
    print("=" * 80)

    if not OPENAI_API_KEY:
        print(
            "⚠️  ADVERTENCIA: OPENAI_API_KEY no encontrada. Se usarán mensajes fallback."
        )
        print("   Para usar IA, exporta: export OPENAI_API_KEY='tu-api-key'")
        print()

    # Crear engine
    engine = create_engine(DB_DSN, echo=False)

    # Crear tabla si no existe
    print("🔧 Verificando tablas...")
    SQLModel.metadata.create_all(engine)
    print("✅ Tablas listas.")

    # Obtener eventos para generar reportes
    print(f"\n📊 Buscando eventos para generar {NUM_REPORTS} reportes...")

    with Session(engine) as session:
        # Seleccionar eventos que NO sean APPROVED (más interesante para alertas)
        events = session.query(NormalizedPaymentEvent).filter(
            NormalizedPaymentEvent.status_category.in_(
                ["FAILED", "PENDING", "CANCELLED", "UNPROCESSED"]
            )
        ).limit(NUM_REPORTS * 2).all()

        if not events:
            print("❌ No se encontraron eventos en la base de datos.")
            print("   Ejecuta primero: python normalized_db_injector.py")
            return

        # Tomar una muestra aleatoria
        selected_events = random.sample(events, min(NUM_REPORTS, len(events)))

        print(
            f"✅ Encontrados {len(events)} eventos, seleccionados {len(selected_events)}"
        )
        print(f"\n🤖 Generando análisis con IA...")

        reports = []
        for i, event in enumerate(selected_events, 1):
            print(
                f"   [{i}/{len(selected_events)}] Analizando evento {event.id} ({event.status_category})..."
            )

            # Generar análisis con IA
            explanation, recommendation = generate_ai_analysis(event)

            # Crear reporte
            report = AlertReport(
                id=uuid4(),
                normalized_event_id=event.id,
                ai_explanation=explanation,
                ai_recommendation=recommendation,
                status="pending",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            reports.append(report)

            if (i) % 10 == 0:
                print(f"   ✓ Procesados {i}/{len(selected_events)}...")

        # Insertar todos los reportes
        print(f"\n💾 Insertando {len(reports)} reportes en la base de datos...")
        session.add_all(reports)
        session.commit()

        print(f"\n{'='*80}")
        print(f"✅ ¡COMPLETADO! {len(reports)} reportes generados exitosamente")
        print(f"{'='*80}")

        # Estadísticas
        print("\n📊 Estadísticas:")
        print(f"   Total de reportes: {len(reports)}")
        print(f"   Estado: Todos en 'pending'")
        print(
            f"   Próximo paso: Usa los endpoints de la API para revisar y actualizar los reportes"
        )
        print()


if __name__ == "__main__":
    main()
