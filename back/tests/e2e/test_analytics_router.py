"""
E2E tests for Analytics Router

Tests end-to-end para los endpoints de analytics.
Verifica paginación, filtros y respuestas correctas.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.domain.models.enums import ErrorSource, FailureReason, NormalizationMethod, PaymentStatus
from app.domain.models.payment_event import NormalizedPaymentEvent
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Fixture para TestClient"""
    return TestClient(app)


@pytest.fixture
def sample_events_for_analytics(session: Session) -> list[NormalizedPaymentEvent]:
    """Crear múltiples eventos para probar paginación"""
    now = datetime.now(UTC)
    events = []

    # Crear 25 eventos de prueba con variedad
    for i in range(25):
        provider = ["stripe", "adyen", "paypal"][i % 3]
        status = [PaymentStatus.APPROVED, PaymentStatus.DECLINED, PaymentStatus.ERROR][i % 3]
        country = ["US", "MX", "BR"][i % 3]

        event = NormalizedPaymentEvent(
            id=uuid4(),
            merchant_name=f"Merchant {i % 5}",
            provider=provider,
            country=country,
            status_category=status,
            failure_reason=FailureReason.INSUFFICIENT_FUNDS
            if status != PaymentStatus.APPROVED
            else None,
            error_source=ErrorSource.CUSTOMER if status != PaymentStatus.APPROVED else None,
            amount=Decimal(f"{100 + i * 10}.00"),
            currency="USD",
            amount_usd_equivalent=Decimal(f"{100 + i * 10}.00"),
            http_status_code=200 if status == PaymentStatus.APPROVED else 402,
            normalization_method=NormalizationMethod.RULE_BASED,
            created_at=now - timedelta(hours=i),
            updated_at=now - timedelta(hours=i),
        )
        events.append(event)
        session.add(event)

    session.commit()

    for event in events:
        session.refresh(event)

    return events


class TestAnalyticsRouter:
    """Tests E2E para Analytics Router"""

    def test_get_metrics_summary(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/metrics/summary"""
        response = client.get("/api/analytics/metrics/summary")

        assert response.status_code == 200
        data = response.json()

        # Verificar estructura
        assert "total_events" in data
        assert "success_rate" in data
        assert "status_distribution" in data
        assert "top_failure_reasons" in data
        assert "provider_distribution" in data
        assert "transaction_volume_usd" in data
        assert "error_source_distribution" in data
        assert "period" in data

        # Verificar valores
        assert data["total_events"] >= 25
        assert isinstance(data["success_rate"], (int, float))
        assert 0 <= data["success_rate"] <= 100

    def test_get_metrics_summary_with_date_range(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/metrics/summary con rango de fechas"""
        now = datetime.now(UTC)
        start_date = (now - timedelta(hours=5)).isoformat()
        end_date = now.isoformat()

        response = client.get(
            f"/api/analytics/metrics/summary?start_date={start_date}&end_date={end_date}"
        )

        assert response.status_code == 200
        data = response.json()

        # Debería filtrar eventos
        assert data["total_events"] <= 25
        assert data["period"]["start"] is not None
        assert data["period"]["end"] is not None

    def test_get_provider_metrics(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/metrics/providers/{provider}"""
        response = client.get("/api/analytics/metrics/providers/stripe")

        assert response.status_code == 200
        data = response.json()

        # Verificar estructura
        assert data["provider"] == "stripe"
        assert "total_events" in data
        assert "success_rate" in data
        assert "status_distribution" in data
        assert "failure_reasons" in data
        assert "transaction_volume_usd" in data

        # Verificar que hay eventos
        assert data["total_events"] > 0

    def test_get_provider_metrics_nonexistent(
        self,
        client: TestClient,
    ):
        """Test: GET /analytics/metrics/providers/{provider} - provider inexistente"""
        response = client.get("/api/analytics/metrics/providers/nonexistent")

        assert response.status_code == 200
        data = response.json()

        assert data["total_events"] == 0
        assert "message" in data

    def test_get_failure_analysis(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/failures"""
        response = client.get("/api/analytics/failures")

        assert response.status_code == 200
        data = response.json()

        # Verificar estructura
        assert "top_failure_reasons" in data
        assert "error_source_distribution" in data
        assert "http_status_codes" in data
        assert "period" in data

        # Verificar que hay datos
        assert len(data["top_failure_reasons"]) > 0

    def test_get_failure_analysis_with_limit(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/failures con limit"""
        response = client.get("/api/analytics/failures?limit=5")

        assert response.status_code == 200
        data = response.json()

        # Verificar que respeta el límite
        assert len(data["top_failure_reasons"]) <= 5

    def test_get_recent_events_pagination(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/events/recent - paginación"""
        # Primera página
        response = client.get("/api/analytics/events/recent?skip=0&limit=10")

        assert response.status_code == 200
        data = response.json()

        # Verificar estructura de paginación
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert "events" in data

        assert data["skip"] == 0
        assert data["limit"] == 10
        assert len(data["events"]) <= 10
        assert data["total"] >= 25

        # Verificar orden descendente (más reciente primero)
        if len(data["events"]) > 1:
            first_date = datetime.fromisoformat(data["events"][0]["created_at"])
            second_date = datetime.fromisoformat(data["events"][1]["created_at"])
            assert first_date >= second_date

        # Segunda página
        response2 = client.get("/api/analytics/events/recent?skip=10&limit=10")
        assert response2.status_code == 200
        data2 = response2.json()

        assert data2["skip"] == 10
        assert data2["limit"] == 10
        assert len(data2["events"]) <= 10

        # Verificar que son eventos diferentes
        first_page_ids = {event["id"] for event in data["events"]}
        second_page_ids = {event["id"] for event in data2["events"]}
        assert first_page_ids.isdisjoint(second_page_ids)

    def test_get_recent_events_with_filters(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/events/recent con filtros"""
        # Filtrar por provider
        response = client.get("/api/analytics/events/recent?provider=stripe")

        assert response.status_code == 200
        data = response.json()

        # Verificar que todos los eventos son de stripe
        for event in data["events"]:
            assert event["provider"] == "stripe"

        # Filtrar por status
        response2 = client.get("/api/analytics/events/recent?status=approved")

        assert response2.status_code == 200
        data2 = response2.json()

        # Verificar que todos los eventos están approved
        for event in data2["events"]:
            assert event["status_category"] == PaymentStatus.APPROVED.value

        # Filtrar por ambos
        response3 = client.get("/api/analytics/events/recent?provider=stripe&status=approved")

        assert response3.status_code == 200
        data3 = response3.json()

        for event in data3["events"]:
            assert event["provider"] == "stripe"
            assert event["status_category"] == PaymentStatus.APPROVED.value

    def test_get_events_by_merchant(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/events/by-merchant/{merchant_name}"""
        response = client.get("/api/analytics/events/by-merchant/Merchant%200")

        assert response.status_code == 200
        data = response.json()

        # Verificar estructura
        assert "merchant_name" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert "events" in data

        assert data["merchant_name"] == "Merchant 0"

        # Verificar que todos los eventos son del merchant
        for event in data["events"]:
            # La estructura del response no incluye merchant_name en este endpoint
            # Solo verifica que retorna eventos
            assert "id" in event
            assert "provider" in event

    def test_get_events_by_merchant_pagination(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/events/by-merchant con paginación"""
        response = client.get("/api/analytics/events/by-merchant/Merchant%200?skip=0&limit=2")

        assert response.status_code == 200
        data = response.json()

        assert data["skip"] == 0
        assert data["limit"] == 2
        assert len(data["events"]) <= 2

        # Verificar orden descendente
        if len(data["events"]) > 1:
            first_date = datetime.fromisoformat(data["events"][0]["created_at"])
            second_date = datetime.fromisoformat(data["events"][1]["created_at"])
            assert first_date >= second_date

    def test_get_events_by_country(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/events/by-country/{country}"""
        response = client.get("/api/analytics/events/by-country/US")

        assert response.status_code == 200
        data = response.json()

        # Verificar estructura
        assert "country" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert "events" in data

        assert data["country"] == "US"
        assert data["total"] > 0

        # Verificar que todos los eventos son de US
        for event in data["events"]:
            # country no está en el response, pero verificamos que retorna datos
            assert "id" in event
            assert "merchant_name" in event

    def test_get_events_by_country_pagination(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/events/by-country con paginación"""
        response = client.get("/api/analytics/events/by-country/MX?skip=0&limit=5")

        assert response.status_code == 200
        data = response.json()

        assert data["skip"] == 0
        assert data["limit"] == 5
        assert len(data["events"]) <= 5

        # Verificar orden descendente
        if len(data["events"]) > 1:
            first_date = datetime.fromisoformat(data["events"][0]["created_at"])
            second_date = datetime.fromisoformat(data["events"][1]["created_at"])
            assert first_date >= second_date

    def test_pagination_limit_validation(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: Validación de límite máximo en paginación"""
        # Intentar con límite > 100 (debería fallar o ajustar)
        response = client.get("/api/analytics/events/recent?limit=200")

        # Dependiendo de la validación, puede retornar 422 o ajustar a 100
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            # Si ajusta automáticamente, debería ser máximo 100
            assert len(data["events"]) <= 100

    def test_get_all_providers(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/providers - lista de providers únicos"""
        response = client.get("/api/analytics/providers")

        assert response.status_code == 200
        data = response.json()

        # Verificar estructura
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert "providers" in data

        # Debería haber al menos 3 providers (stripe, adyen, paypal)
        assert data["total"] >= 3
        assert len(data["providers"]) >= 3

        # Verificar que son strings
        for provider in data["providers"]:
            assert isinstance(provider, str)

        # Verificar orden descendente
        if len(data["providers"]) > 1:
            assert data["providers"] == sorted(data["providers"], reverse=True)

    def test_get_all_providers_pagination(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/providers con paginación"""
        response = client.get("/api/analytics/providers?skip=0&limit=2")

        assert response.status_code == 200
        data = response.json()

        assert data["skip"] == 0
        assert data["limit"] == 2
        assert len(data["providers"]) <= 2

        # Segunda página
        response2 = client.get("/api/analytics/providers?skip=2&limit=2")
        assert response2.status_code == 200
        data2 = response2.json()

        assert data2["skip"] == 2

        # Verificar que son providers diferentes
        if len(data["providers"]) > 0 and len(data2["providers"]) > 0:
            first_page = set(data["providers"])
            second_page = set(data2["providers"])
            assert first_page.isdisjoint(second_page)

    def test_get_all_merchants(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/merchants - lista de merchants únicos"""
        response = client.get("/api/analytics/merchants")

        assert response.status_code == 200
        data = response.json()

        # Verificar estructura
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert "merchants" in data

        # Debería haber al menos 5 merchants (Merchant 0-4)
        assert data["total"] >= 5
        assert len(data["merchants"]) >= 5

        # Verificar que son strings
        for merchant in data["merchants"]:
            assert isinstance(merchant, str)

        # Verificar orden descendente
        if len(data["merchants"]) > 1:
            assert data["merchants"] == sorted(data["merchants"], reverse=True)

    def test_get_all_merchants_pagination(
        self,
        client: TestClient,
        sample_events_for_analytics: list[NormalizedPaymentEvent],
    ):
        """Test: GET /analytics/merchants con paginación"""
        response = client.get("/api/analytics/merchants?skip=0&limit=3")

        assert response.status_code == 200
        data = response.json()

        assert data["skip"] == 0
        assert data["limit"] == 3
        assert len(data["merchants"]) <= 3

        # Segunda página
        response2 = client.get("/api/analytics/merchants?skip=3&limit=3")
        assert response2.status_code == 200
        data2 = response2.json()

        assert data2["skip"] == 3

        # Verificar que son merchants diferentes
        if len(data["merchants"]) > 0 and len(data2["merchants"]) > 0:
            first_page = set(data["merchants"])
            second_page = set(data2["merchants"])
            assert first_page.isdisjoint(second_page)
