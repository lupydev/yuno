"""Tests unitarios para schemas de API"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.models.enums import FailureReason, NormalizationMethod, PaymentStatus
from app.domain.schemas.api_schemas import (
    EventDetailResponse,
    EventIngestRequest,
    EventIngestResponse,
)


class TestEventIngestRequest:
    """Tests para EventIngestRequest"""

    def test_create_request_success(self):
        """Verifica que se pueda crear un EventIngestRequest válido"""
        data = {
            "raw_event": {"status": "succeeded", "amount": 100},
            "provider": "stripe",
        }

        request = EventIngestRequest(**data)

        assert request.raw_event == {"status": "succeeded", "amount": 100}
        assert request.provider == "stripe"

    def test_raw_event_cannot_be_empty(self):
        """Verifica que raw_event no pueda estar vacío"""
        data = {"raw_event": {}}

        with pytest.raises(ValidationError) as exc_info:
            EventIngestRequest(**data)
        assert "raw_event cannot be empty" in str(exc_info.value)

    def test_provider_is_optional(self):
        """Verifica que provider sea opcional"""
        data = {"raw_event": {"status": "succeeded"}}

        request = EventIngestRequest(**data)

        assert request.raw_event == {"status": "succeeded"}
        assert request.provider is None

    def test_raw_event_with_nested_data(self):
        """Verifica que raw_event acepte datos anidados"""
        data = {
            "raw_event": {
                "payment": {"id": "pay_123", "amount": 1000, "currency": "USD"},
                "customer": {"name": "John Doe", "email": "john@example.com"},
            }
        }

        request = EventIngestRequest(**data)

        assert request.raw_event["payment"]["id"] == "pay_123"
        assert request.raw_event["customer"]["name"] == "John Doe"


class TestEventIngestResponse:
    """Tests para EventIngestResponse"""

    def test_create_response_success(self):
        """Verifica que se pueda crear un EventIngestResponse válido"""
        event_id = uuid4()
        data = {
            "id": event_id,
            "status": PaymentStatus.APPROVED,
            "normalization_method": NormalizationMethod.AI_BASED,
            "confidence_score": 0.95,
        }

        response = EventIngestResponse(**data)

        assert response.id == event_id
        assert response.status == PaymentStatus.APPROVED
        assert response.normalization_method == NormalizationMethod.AI_BASED
        assert response.confidence_score == 0.95
        assert response.message == "Event ingested successfully"

    def test_confidence_score_is_optional(self):
        """Verifica que confidence_score sea opcional"""
        event_id = uuid4()
        data = {
            "id": event_id,
            "status": PaymentStatus.APPROVED,
            "normalization_method": NormalizationMethod.RULE_BASED,
        }

        response = EventIngestResponse(**data)

        assert response.id == event_id
        assert response.confidence_score is None

    def test_custom_message(self):
        """Verifica que se pueda personalizar el mensaje"""
        event_id = uuid4()
        data = {
            "id": event_id,
            "status": PaymentStatus.PENDING,
            "normalization_method": NormalizationMethod.MANUAL,
            "message": "Event pending review",
        }

        response = EventIngestResponse(**data)

        assert response.message == "Event pending review"

    def test_different_statuses(self):
        """Verifica diferentes estados de pago"""
        event_id = uuid4()

        for status in [
            PaymentStatus.APPROVED,
            PaymentStatus.FAILED,
            PaymentStatus.PENDING,
            PaymentStatus.UNPROCESSED,
        ]:
            data = {
                "id": event_id,
                "status": status,
                "normalization_method": NormalizationMethod.AI_BASED,
            }

            response = EventIngestResponse(**data)
            assert response.status == status


class TestEventDetailResponse:
    """Tests para EventDetailResponse"""

    @pytest.fixture
    def valid_event_detail_data(self):
        """Datos válidos para EventDetailResponse"""
        return {
            "id": uuid4(),
            "merchant_name": "Acme Corp",
            "provider": "stripe",
            "country": "US",
            "status_category": PaymentStatus.APPROVED,
            "failure_reason": None,
            "amount": Decimal("199.99"),
            "currency": "USD",
            "amount_usd_equivalent": Decimal("199.99"),
            "provider_transaction_id": "ch_3abc123",
            "normalization_method": NormalizationMethod.AI_BASED,
            "confidence_score": 0.95,
            "created_at": datetime.now(UTC),
            "normalized_at": datetime.now(UTC),
            "event_metadata": {"payment_method": "card"},
        }

    def test_create_detail_response_success(self, valid_event_detail_data):
        """Verifica que se pueda crear un EventDetailResponse válido"""
        response = EventDetailResponse(**valid_event_detail_data)

        assert response.merchant_name == "Acme Corp"
        assert response.provider == "stripe"
        assert response.country == "US"
        assert response.status_category == PaymentStatus.APPROVED
        assert response.amount == Decimal("199.99")
        assert response.currency == "USD"
        assert response.amount_usd_equivalent == Decimal("199.99")
        assert response.normalization_method == NormalizationMethod.AI_BASED

    def test_failed_payment_with_failure_reason(self, valid_event_detail_data):
        """Verifica un pago fallido con razón de fallo"""
        data = valid_event_detail_data.copy()
        data["status_category"] = PaymentStatus.FAILED
        data["failure_reason"] = FailureReason.CARD_DECLINED

        response = EventDetailResponse(**data)

        assert response.status_category == PaymentStatus.FAILED
        assert response.failure_reason == FailureReason.CARD_DECLINED

    def test_optional_fields(self, valid_event_detail_data):
        """Verifica que los campos opcionales funcionen correctamente"""
        data = valid_event_detail_data.copy()
        data["failure_reason"] = None
        data["provider_transaction_id"] = None
        data["confidence_score"] = None
        data["event_metadata"] = None

        response = EventDetailResponse(**data)

        assert response.failure_reason is None
        assert response.provider_transaction_id is None
        assert response.confidence_score is None
        assert response.event_metadata is None

    def test_timestamp_fields(self, valid_event_detail_data):
        """Verifica que los timestamps estén presentes"""
        response = EventDetailResponse(**valid_event_detail_data)

        assert isinstance(response.created_at, datetime)
        assert isinstance(response.normalized_at, datetime)

    def test_event_metadata_structure(self, valid_event_detail_data):
        """Verifica que event_metadata pueda contener datos estructurados"""
        data = valid_event_detail_data.copy()
        data["event_metadata"] = {
            "payment_method": "card",
            "card_brand": "visa",
            "card_last4": "4242",
            "customer_id": "cus_123",
        }

        response = EventDetailResponse(**data)

        assert response.event_metadata["payment_method"] == "card"
        assert response.event_metadata["card_brand"] == "visa"
        assert response.event_metadata["card_last4"] == "4242"

    def test_different_normalization_methods(self, valid_event_detail_data):
        """Verifica diferentes métodos de normalización"""
        for method in NormalizationMethod:
            data = valid_event_detail_data.copy()
            data["normalization_method"] = method

            response = EventDetailResponse(**data)
            assert response.normalization_method == method

    def test_from_attributes_config(self):
        """Verifica que from_attributes esté habilitado en Config"""
        assert EventDetailResponse.model_config.get("from_attributes") is True
