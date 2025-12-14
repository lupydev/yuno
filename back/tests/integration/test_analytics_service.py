"""
Integration tests for Analytics Service

Tests de integración para el servicio de analítica.
Verifica queries, agregaciones y cálculos de métricas.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlmodel import Session

from app.domain.models.enums import ErrorSource, FailureReason, NormalizationMethod, PaymentStatus
from app.domain.models.payment_event import NormalizedPaymentEvent
from app.services.analytics_service import AnalyticsService


@pytest.fixture
def analytics_service(session: Session) -> AnalyticsService:
    """Fixture para AnalyticsService"""
    return AnalyticsService(session)


@pytest.fixture
def sample_events(session: Session) -> list[NormalizedPaymentEvent]:
    """Crear eventos de prueba en la DB"""
    now = datetime.now(UTC)

    events = [
        # Evento 1: Approved - Stripe
        NormalizedPaymentEvent(
            id=uuid4(),
            merchant_name="Test Merchant 1",
            provider="stripe",
            country="US",
            status_category=PaymentStatus.APPROVED,
            failure_reason=None,
            error_source=None,
            amount=Decimal("100.00"),
            currency="USD",
            amount_usd_equivalent=Decimal("100.00"),
            http_status_code=200,
            normalization_method=NormalizationMethod.RULE_BASED,
            created_at=now - timedelta(hours=1),
            updated_at=now - timedelta(hours=1),
        ),
        # Evento 2: Declined - Stripe
        NormalizedPaymentEvent(
            id=uuid4(),
            merchant_name="Test Merchant 1",
            provider="stripe",
            country="US",
            status_category=PaymentStatus.DECLINED,
            failure_reason=FailureReason.INSUFFICIENT_FUNDS,
            error_source=ErrorSource.CUSTOMER,
            amount=Decimal("50.00"),
            currency="USD",
            amount_usd_equivalent=Decimal("50.00"),
            http_status_code=402,
            normalization_method=NormalizationMethod.RULE_BASED,
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(hours=2),
        ),
        # Evento 3: Approved - Adyen
        NormalizedPaymentEvent(
            id=uuid4(),
            merchant_name="Test Merchant 2",
            provider="adyen",
            country="MX",
            status_category=PaymentStatus.APPROVED,
            failure_reason=None,
            error_source=None,
            amount=Decimal("200.00"),
            currency="MXN",
            amount_usd_equivalent=Decimal("10.00"),  # ~20 MXN = 1 USD
            http_status_code=200,
            normalization_method=NormalizationMethod.AI_EXTRACTED,
            created_at=now - timedelta(hours=3),
            updated_at=now - timedelta(hours=3),
        ),
        # Evento 4: Error - Adyen
        NormalizedPaymentEvent(
            id=uuid4(),
            merchant_name="Test Merchant 2",
            provider="adyen",
            country="MX",
            status_category=PaymentStatus.ERROR,
            failure_reason=FailureReason.GATEWAY_ERROR,
            error_source=ErrorSource.PROVIDER,
            amount=Decimal("150.00"),
            currency="MXN",
            amount_usd_equivalent=Decimal("7.50"),
            http_status_code=500,
            normalization_method=NormalizationMethod.AI_EXTRACTED,
            created_at=now - timedelta(hours=4),
            updated_at=now - timedelta(hours=4),
        ),
        # Evento 5: Approved - PayPal
        NormalizedPaymentEvent(
            id=uuid4(),
            merchant_name="Test Merchant 3",
            provider="paypal",
            country="BR",
            status_category=PaymentStatus.APPROVED,
            failure_reason=None,
            error_source=None,
            amount=Decimal("300.00"),
            currency="BRL",
            amount_usd_equivalent=Decimal("60.00"),  # ~5 BRL = 1 USD
            http_status_code=200,
            normalization_method=NormalizationMethod.RULE_BASED,
            created_at=now - timedelta(hours=5),
            updated_at=now - timedelta(hours=5),
        ),
    ]

    for event in events:
        session.add(event)

    session.commit()

    for event in events:
        session.refresh(event)

    return events


class TestAnalyticsService:
    """Tests para AnalyticsService"""

    def test_get_metrics_summary(
        self,
        analytics_service: AnalyticsService,
        sample_events: list[NormalizedPaymentEvent],
    ):
        """Test: Obtener resumen de métricas"""
        metrics = analytics_service.get_metrics_summary()

        # Verificar que retorna datos
        assert metrics is not None
        assert "total_events" in metrics
        assert "success_rate" in metrics
        assert "status_distribution" in metrics
        assert "top_failure_reasons" in metrics
        assert "provider_distribution" in metrics
        assert "transaction_volume_usd" in metrics
        assert "error_source_distribution" in metrics

        # Verificar valores
        assert metrics["total_events"] == 5
        assert metrics["success_rate"] == 60.0  # 3 approved de 5 total = 60%

        # Verificar distribución de status
        status_dist = metrics["status_distribution"]
        assert status_dist[PaymentStatus.APPROVED.value] == 3
        assert status_dist[PaymentStatus.DECLINED.value] == 1
        assert status_dist[PaymentStatus.ERROR.value] == 1

        # Verificar distribución de providers
        provider_dist = metrics["provider_distribution"]
        assert len(provider_dist) == 3

        # Verificar volumen
        volume = metrics["transaction_volume_usd"]
        assert volume["transaction_count"] == 5
        assert volume["total_usd"] > 0

    def test_get_metrics_summary_with_date_range(
        self,
        analytics_service: AnalyticsService,
        sample_events: list[NormalizedPaymentEvent],
    ):
        """Test: Obtener métricas con rango de fechas"""
        now = datetime.now(UTC)
        start_date = now - timedelta(hours=3)
        end_date = now

        metrics = analytics_service.get_metrics_summary(start_date, end_date)

        # Solo debería incluir los eventos de las últimas 3 horas (3 eventos)
        assert metrics["total_events"] == 3
        assert metrics["period"]["start"] is not None
        assert metrics["period"]["end"] is not None

    def test_get_provider_stats(
        self,
        analytics_service: AnalyticsService,
        sample_events: list[NormalizedPaymentEvent],
    ):
        """Test: Obtener estadísticas de un provider"""
        stats = analytics_service.get_provider_stats("stripe")

        # Verificar datos
        assert stats is not None
        assert stats["provider"] == "stripe"
        assert stats["total_events"] == 2  # 1 approved + 1 declined
        assert stats["success_rate"] == 50.0  # 1 de 2

        # Verificar failure reasons
        failures = stats["failure_reasons"]
        assert len(failures) > 0
        assert failures[0]["reason"] == FailureReason.INSUFFICIENT_FUNDS.value

    def test_get_provider_stats_nonexistent(
        self,
        analytics_service: AnalyticsService,
        sample_events: list[NormalizedPaymentEvent],
    ):
        """Test: Estadísticas de provider que no existe"""
        stats = analytics_service.get_provider_stats("nonexistent")

        assert stats["total_events"] == 0
        assert "message" in stats

    def test_get_failure_analysis(
        self,
        analytics_service: AnalyticsService,
        sample_events: list[NormalizedPaymentEvent],
    ):
        """Test: Análisis de fallos"""
        analysis = analytics_service.get_failure_analysis()

        # Verificar estructura
        assert "top_failure_reasons" in analysis
        assert "error_source_distribution" in analysis
        assert "http_status_codes" in analysis

        # Verificar failure reasons
        top_failures = analysis["top_failure_reasons"]
        assert len(top_failures) > 0

        # Verificar error sources
        error_sources = analysis["error_source_distribution"]
        assert len(error_sources) > 0

        # Verificar HTTP codes
        http_codes = analysis["http_status_codes"]
        assert len(http_codes) > 0

    def test_success_rate_calculation(
        self,
        analytics_service: AnalyticsService,
    ):
        """Test: Cálculo de success rate"""
        # Test con datos vacíos
        rate = analytics_service._calculate_success_rate({}, 0)
        assert rate == 0.0

        # Test con datos normales
        distribution = {
            PaymentStatus.APPROVED.value: 7,
            PaymentStatus.DECLINED.value: 2,
            PaymentStatus.ERROR.value: 1,
        }
        rate = analytics_service._calculate_success_rate(distribution, 10)
        assert rate == 70.0

        # Test con 100% success
        distribution_100 = {PaymentStatus.APPROVED.value: 10}
        rate = analytics_service._calculate_success_rate(distribution_100, 10)
        assert rate == 100.0

    def test_transaction_volume_calculation(
        self,
        analytics_service: AnalyticsService,
        sample_events: list[NormalizedPaymentEvent],
    ):
        """Test: Cálculo de volumen transaccional"""
        volume = analytics_service._get_transaction_volume()

        assert volume["transaction_count"] == 5
        assert volume["total_usd"] > 0
        assert volume["average_usd"] > 0
        assert volume["total_usd"] == volume["average_usd"] * volume["transaction_count"]

    def test_error_source_distribution(
        self,
        analytics_service: AnalyticsService,
        sample_events: list[NormalizedPaymentEvent],
    ):
        """Test: Distribución de error sources"""
        distribution = analytics_service._get_error_source_distribution()

        # Debería haber al menos 2 error sources (CUSTOMER y PROVIDER)
        assert len(distribution) >= 2

        sources = [item["source"] for item in distribution]
        assert ErrorSource.CUSTOMER.value in sources
        assert ErrorSource.PROVIDER.value in sources
