"""
Script para generar e insertar datos normalizados de pagos en PostgreSQL

Este script genera datos simulados que representan pagos ya normalizados
siguiendo el esquema de NormalizedPaymentEvent con campos realistas y
compatibles con los schemas del backend.
"""

import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from enums import FailureReason, NormalizationMethod, PaymentStatus
from models import NormalizedPaymentEvent

# --- CONFIGURATION ---
DB_DSN = "postgresql://postgres:OymPLdKHtAnAcRyRpjQyPhpCqHMjpsgv@maglev.proxy.rlwy.net:33322/railway"
TOTAL_RECORDS = 2000  # Incrementado para datos masivos

# Master Data Realista
MERCHANTS = [
    "Shopito",
    "Rappi",
    "MercadoLibre",
    "CornerShop",
    "Falabella",
    "GameStore",
    "Netflix",
    "Amazon",
    "Uber",
    "Spotify",
    "DiDi",
    "iFood",
    "Zara",
    "H&M",
    "Apple",
    "Samsung",
    "Nike",
    "Adidas",
    "Booking.com",
    "Airbnb",
]

PROVIDERS = [
    "stripe",
    "dlocal",
    "payu",
    "adyen",
    "kushki",
    "mercadopago",
    "paypal",
    "wompi",
    "ebanx",
    "getnet",
]

COUNTRIES = ["MX", "CO", "PE", "CL", "AR", "BR", "US", "ES", "EC", "UY"]
CURRENCIES = {
    "MX": "MXN",
    "CO": "COP",
    "PE": "PEN",
    "CL": "CLP",
    "AR": "ARS",
    "BR": "BRL",
    "US": "USD",
    "ES": "EUR",
    "EC": "USD",
    "UY": "UYU",
}

# Distribución de escenarios (probabilidades realistas)
# 80% aprobados, 12% fallidos, 4% pendientes, 4% otros
SCENARIO_WEIGHTS = {
    PaymentStatus.APPROVED: 0.80,
    PaymentStatus.FAILED: 0.12,
    PaymentStatus.PENDING: 0.04,
    PaymentStatus.CANCELLED: 0.02,
    PaymentStatus.REFUNDED: 0.01,
    PaymentStatus.UNPROCESSED: 0.01,
}


def generate_normalized_payment() -> NormalizedPaymentEvent:
    """Genera un evento de pago normalizado con datos realistas y completos"""

    # Seleccionar datos básicos
    merchant_name = random.choice(MERCHANTS)
    provider = random.choice(PROVIDERS)
    country = random.choice(COUNTRIES)
    currency = CURRENCIES[country]

    # Seleccionar status basado en pesos
    status_category = random.choices(
        list(SCENARIO_WEIGHTS.keys()), weights=list(SCENARIO_WEIGHTS.values())
    )[0]

    # Generar datos financieros
    amount = Decimal(str(round(random.uniform(10.0, 5000.0), 2)))
    latency_ms = random.randint(50, 3000)

    # Inicializar variables de estado
    failure_reason = None
    provider_status = None
    confidence_score = random.uniform(0.85, 1.0)

    # --- APPROVED: Transacciones exitosas ---
    if status_category == PaymentStatus.APPROVED:
        provider_status = random.choice(
            ["approved", "authorized", "succeeded", "completed", "00_success", "paid"]
        )
        failure_reason = None
        confidence_score = random.uniform(0.90, 1.0)

    # --- FAILED: Transacciones fallidas por distintas razones ---
    elif status_category == PaymentStatus.FAILED:
        # Diferentes razones de fallo
        failure_reason = random.choice(
            [
                FailureReason.INSUFFICIENT_FUNDS,
                FailureReason.CARD_DECLINED,
                FailureReason.EXPIRED_CARD,
                FailureReason.INVALID_CARD,
                FailureReason.BLOCKED_CARD,
                FailureReason.FRAUD_SUSPECTED,
                FailureReason.SECURITY_VIOLATION,
                FailureReason.PROVIDER_ERROR,
                FailureReason.TIMEOUT,
                FailureReason.NETWORK_ERROR,
                FailureReason.INVALID_MERCHANT,
                FailureReason.CONFIGURATION_ERROR,
                FailureReason.DUPLICATE_TRANSACTION,
                FailureReason.AMOUNT_EXCEEDED,
            ]
        )

        provider_status = random.choice(
            [
                "card_declined",
                "insufficient_funds",
                "do_not_honor",
                "expired_card",
                "invalid_card",
                "fraud_suspected",
                "timeout",
                "gateway_error",
                "network_error",
            ]
        )
        confidence_score = random.uniform(0.80, 0.95)
        latency_ms = random.randint(100, 2000)

    # --- PENDING: Transacciones pendientes de confirmación ---
    elif status_category == PaymentStatus.PENDING:
        provider_status = random.choice(
            [
                "pending",
                "processing",
                "awaiting_confirmation",
                "in_progress",
                "pending_capture",
            ]
        )
        failure_reason = None
        confidence_score = random.uniform(0.70, 0.90)
        latency_ms = random.randint(200, 5000)

    # --- CANCELLED: Transacciones canceladas ---
    elif status_category == PaymentStatus.CANCELLED:
        provider_status = random.choice(["cancelled", "canceled", "voided", "aborted"])
        failure_reason = None
        confidence_score = random.uniform(0.85, 0.98)

    # --- REFUNDED: Transacciones reembolsadas ---
    elif status_category == PaymentStatus.REFUNDED:
        provider_status = random.choice(["refunded", "reversed", "chargeback"])
        failure_reason = None
        confidence_score = random.uniform(0.90, 1.0)

    # --- UNPROCESSED: No se pudo normalizar ---
    elif status_category == PaymentStatus.UNPROCESSED:
        provider_status = random.choice(
            ["unknown", "unrecognized", "invalid_format", "parsing_error"]
        )
        failure_reason = FailureReason.UNKNOWN
        confidence_score = random.uniform(0.30, 0.70)
        latency_ms = random.randint(50, 500)

    # Generar transaction ID
    provider_transaction_id = f"{provider}_{uuid4().hex[:16]}"

    # Generar método de normalización con distribución realista
    normalization_method = random.choices(
        [
            NormalizationMethod.AI_BASED,
            NormalizationMethod.RULE_BASED,
            NormalizationMethod.HYBRID,
            NormalizationMethod.MANUAL,
        ],
        weights=[0.30, 0.50, 0.15, 0.05],
    )[0]

    # Generar raw_data simulando datos originales del provider
    raw_data = {
        "provider": provider,
        "original_status": provider_status,
        "amount": float(amount),
        "currency": currency,
        "country": country,
        "merchant": merchant_name,
        "transaction_id": provider_transaction_id,
        "timestamp": (
            datetime.now(UTC) - timedelta(days=random.randint(0, 60))
        ).isoformat(),
        "format": random.choice(["modern", "legacy", "nested", "flat"]),
        "version": random.choice(["v1", "v2", "v3"]),
        "webhook_id": f"wh_{uuid4().hex[:10]}",
    }

    # Metadata adicional realista
    event_metadata = {
        "ip_country": random.choice(COUNTRIES),
        "device_type": random.choice(["mobile", "desktop", "tablet"]),
        "device_os": random.choice(["iOS", "Android", "Windows", "macOS", "Linux"]),
        "payment_method": random.choice(
            ["credit_card", "debit_card", "bank_transfer", "wallet", "pix", "boleto"]
        ),
        "card_brand": random.choice(
            ["visa", "mastercard", "amex", "elo", "diners", None]
        ),
        "3ds_enabled": random.choice([True, False]),
        "installments": random.choice([1, 3, 6, 12, None]),
        "browser": random.choice(["Chrome", "Safari", "Firefox", "Edge", None]),
        "session_id": f"sess_{uuid4().hex[:16]}",
        "customer_id": f"cust_{uuid4().hex[:12]}",
    }

    # Generar timestamps con variación realista (últimos 60 días)
    created_at = datetime.now(UTC) - timedelta(
        days=random.randint(0, 60),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    normalized_at = created_at + timedelta(
        seconds=random.randint(1, 600)  # Normalización entre 1 seg y 10 min después
    )

    return NormalizedPaymentEvent(
        id=uuid4(),
        merchant_name=merchant_name,
        provider=provider,
        country=country,
        status_category=status_category,
        failure_reason=failure_reason,
        amount=amount,
        currency=currency,
        provider_transaction_id=provider_transaction_id,
        provider_status=provider_status,
        latency_ms=latency_ms,
        raw_data=raw_data,
        normalization_method=normalization_method,
        confidence_score=confidence_score,
        event_metadata=event_metadata,
        created_at=created_at,
        normalized_at=normalized_at,
        updated_at=normalized_at,
    )


def setup_database(engine):
    """Crea la tabla si no existe"""
    print("🔧 Setting up the database...")
    SQLModel.metadata.create_all(engine)
    print("✅ Table ready.")


def main():
    """Función principal para generar e insertar datos masivos"""
    print("=" * 80)
    print("📊 YUNO - Generador de Datos Normalizados de Pagos")
    print("=" * 80)

    # Crear engine
    engine = create_engine(DB_DSN, echo=False)

    # Setup database
    setup_database(engine)

    print(f"\n🚀 Generando {TOTAL_RECORDS:,} eventos de pago normalizados...")
    print(f"📅 Rango temporal: últimos 60 días")
    print(f"🌎 Países: {', '.join(COUNTRIES)}")
    print(f"🏪 Merchants: {len(MERCHANTS)}")
    print(f"💳 Providers: {len(PROVIDERS)}")

    # Generar registros
    events = []
    batch_size = 1000
    start_time = datetime.now(UTC)

    for i in range(TOTAL_RECORDS):
        event = generate_normalized_payment()
        events.append(event)

        if (i + 1) % batch_size == 0:
            elapsed = (datetime.now(UTC) - start_time).total_seconds()
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            print(
                f"   ✓ Generados {i + 1:,}/{TOTAL_RECORDS:,} eventos... ({rate:.0f} eventos/seg)"
            )

    total_generation_time = (datetime.now(UTC) - start_time).total_seconds()
    print(f"\n✅ Generación completada en {total_generation_time:.2f} segundos")

    # CALCULAR ESTADÍSTICAS ANTES DE INSERTAR (mientras los objetos están en memoria)
    print("\n📊 Calculando estadísticas...")

    # Por status
    status_counts = {}
    for event in events:
        status_counts[event.status_category] = (
            status_counts.get(event.status_category, 0) + 1
        )

    # Por proveedor
    provider_counts = {}
    for event in events:
        provider_counts[event.provider] = provider_counts.get(event.provider, 0) + 1

    # Por país
    country_counts = {}
    for event in events:
        country_counts[event.country] = country_counts.get(event.country, 0) + 1

    # Por método de normalización
    method_counts = {}
    for event in events:
        method_counts[event.normalization_method] = (
            method_counts.get(event.normalization_method, 0) + 1
        )

    # Razones de fallo
    failed_events = [e for e in events if e.status_category == PaymentStatus.FAILED]
    failure_counts = {}
    for event in failed_events:
        if event.failure_reason:
            failure_counts[event.failure_reason] = (
                failure_counts.get(event.failure_reason, 0) + 1
            )

    # Estadísticas financieras
    total_amount = sum(float(e.amount) for e in events)
    avg_amount = total_amount / len(events) if events else 0
    approved_events = [e for e in events if e.status_category == PaymentStatus.APPROVED]
    approved_amount = sum(float(e.amount) for e in approved_events)

    # Insertar en batch
    print(f"\n💾 Insertando {TOTAL_RECORDS:,} registros en PostgreSQL...")
    print("   (Esto puede tardar unos segundos...)")

    try:
        insert_start = datetime.now(UTC)
        with Session(engine) as session:
            # Insertar en batches más pequeños para mejor rendimiento
            for i in range(0, len(events), batch_size):
                batch = events[i : i + batch_size]
                session.add_all(batch)
                session.commit()
                print(
                    f"   ✓ Insertados {min(i + batch_size, len(events)):,}/{len(events):,} registros"
                )

        insert_time = (datetime.now(UTC) - insert_start).total_seconds()
        total_time = total_generation_time + insert_time

        print(f"\n{'='*80}")
        print(f"✅ ¡COMPLETADO! {TOTAL_RECORDS:,} eventos insertados exitosamente")
        print(f"{'='*80}")
        print(f"⏱️  Tiempo de inserción: {insert_time:.2f} segundos")
        print(f"⏱️  Tiempo total: {total_time:.2f} segundos")
        print(f"📈 Tasa promedio: {TOTAL_RECORDS/total_time:.0f} eventos/segundo")

        # MOSTRAR ESTADÍSTICAS (calculadas antes de la inserción)
        print(f"\n{'='*80}")
        print("📊 ESTADÍSTICAS DETALLADAS")
        print(f"{'='*80}")

        # Por status
        print("\n🔹 Por Estado de Pago:")
        for status, count in sorted(
            status_counts.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / TOTAL_RECORDS) * 100
            bar = "█" * int(percentage / 2)
            print(f"   {status.value:12} │ {count:5,} ({percentage:5.1f}%) {bar}")

        # Por proveedor
        print("\n🔹 Top 5 Proveedores:")
        for provider, count in sorted(
            provider_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]:
            percentage = (count / TOTAL_RECORDS) * 100
            print(f"   {provider:15} │ {count:5,} ({percentage:5.1f}%)")

        # Por país
        print("\n🔹 Top 5 Países:")
        for country, count in sorted(
            country_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]:
            percentage = (count / TOTAL_RECORDS) * 100
            print(f"   {country:2} │ {count:5,} ({percentage:5.1f}%)")

        # Por método de normalización
        print("\n🔹 Por Método de Normalización:")
        for method, count in sorted(
            method_counts.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / TOTAL_RECORDS) * 100
            print(f"   {method.value:12} │ {count:5,} ({percentage:5.1f}%)")

        # Estadísticas de fallos
        if failed_events:
            print(f"\n🔹 Top 5 Razones de Fallo ({len(failed_events):,} eventos):")
            for reason, count in sorted(
                failure_counts.items(), key=lambda x: x[1], reverse=True
            )[:5]:
                percentage = (count / len(failed_events)) * 100
                print(f"   {reason.value:25} │ {count:4,} ({percentage:5.1f}%)")

        # Estadísticas financieras
        print(f"\n🔹 Estadísticas Financieras (múltiples monedas):")
        print(f"   Total procesado:  ${total_amount:,.2f}")
        print(f"   Total aprobado:   ${approved_amount:,.2f}")
        print(f"   Ticket promedio:  ${avg_amount:,.2f}")
        print(f"   Tasa de aprob.:   {len(approved_events)/len(events)*100:.1f}%")

        print(f"\n{'='*80}")
        print("✨ Datos generados exitosamente y listos para análisis!")
        print(f"{'='*80}\n")

    except Exception as e:
        print(f"\n❌ ERROR durante la inserción: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
