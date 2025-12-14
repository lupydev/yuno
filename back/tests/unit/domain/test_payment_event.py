"""Tests unitarios para el modelo NormalizedPaymentEvent"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

import pytest

from app.domain.models.enums import FailureReason, NormalizationMethod, PaymentStatus
from app.domain.models.payment_event import NormalizedPaymentEvent


class TestNormalizedPaymentEvent:
    """Tests para el modelo NormalizedPaymentEvent"""

    @pytest.fixture
    def valid_payment_data(self):
        """Datos válidos para crear un evento de pago"""
        return {
            "merchant_name": "Acme Corp",
            "provider": "stripe",
            "country": "US",
            "status_category": PaymentStatus.APPROVED,
            "amount": Decimal("199.99"),
            "currency": "USD",
            "provider_transaction_id": "ch_3abc123",
            "normalization_method": NormalizationMethod.AI_BASED,
            "confidence_score": 0.95,
            "raw_data": {"original": "data"},
        }

    def test_create_payment_event_success(self, valid_payment_data):
        """Verifica que se pueda crear un evento de pago con datos válidos"""
        event = NormalizedPaymentEvent(**valid_payment_data)

        assert event.merchant_name == "Acme Corp"
        assert event.provider == "stripe"
        assert event.country == "US"
        assert event.status_category == PaymentStatus.APPROVED
        assert event.amount == Decimal("199.99")
        assert event.currency == "USD"
        assert event.normalization_method == NormalizationMethod.AI_BASED

    def test_auto_generated_id(self, valid_payment_data):
        """Verifica que el ID se genere automáticamente"""
        event = NormalizedPaymentEvent(**valid_payment_data)

        assert event.id is not None
        assert isinstance(event.id, UUID)

    def test_auto_generated_timestamps(self, valid_payment_data):
        """Verifica que los timestamps se generen automáticamente"""
        event = NormalizedPaymentEvent(**valid_payment_data)

        assert event.created_at is not None
        assert event.normalized_at is not None
        assert event.updated_at is not None
        assert isinstance(event.created_at, datetime)
        assert isinstance(event.normalized_at, datetime)
        assert isinstance(event.updated_at, datetime)

    def test_optional_fields(self, valid_payment_data):
        """Verifica que los campos opcionales funcionen correctamente"""
        # Sin failure_reason
        data = valid_payment_data.copy()
        event = NormalizedPaymentEvent(**data)
        assert event.failure_reason is None

        # Con failure_reason
        data["failure_reason"] = FailureReason.CARD_DECLINED
        event = NormalizedPaymentEvent(**data)
        assert event.failure_reason == FailureReason.CARD_DECLINED

    def test_failed_payment_with_failure_reason(self, valid_payment_data):
        """Verifica un pago fallido con razón de fallo"""
        data = valid_payment_data.copy()
        data["status_category"] = PaymentStatus.FAILED
        data["failure_reason"] = FailureReason.INSUFFICIENT_FUNDS

        event = NormalizedPaymentEvent(**data)

        assert event.status_category == PaymentStatus.FAILED
        assert event.failure_reason == FailureReason.INSUFFICIENT_FUNDS

    def test_event_metadata_field(self, valid_payment_data):
        """Verifica que el campo event_metadata funcione correctamente"""
        data = valid_payment_data.copy()
        data["event_metadata"] = {"payment_method": "card", "card_brand": "visa"}

        event = NormalizedPaymentEvent(**data)

        assert event.event_metadata is not None
        assert event.event_metadata["payment_method"] == "card"
        assert event.event_metadata["card_brand"] == "visa"

    def test_raw_data_field(self, valid_payment_data):
        """Verifica que raw_data almacene el evento original"""
        event = NormalizedPaymentEvent(**valid_payment_data)

        assert event.raw_data == {"original": "data"}

    def test_latency_ms_optional(self, valid_payment_data):
        """Verifica que latency_ms sea opcional"""
        # Sin latency
        event = NormalizedPaymentEvent(**valid_payment_data)
        assert event.latency_ms is None

        # Con latency
        data = valid_payment_data.copy()
        data["latency_ms"] = 150
        event = NormalizedPaymentEvent(**data)
        assert event.latency_ms == 150

    def test_confidence_score_range(self, valid_payment_data):
        """Verifica que confidence_score acepte valores entre 0 y 1"""
        # Score válido
        data = valid_payment_data.copy()
        data["confidence_score"] = 0.75
        event = NormalizedPaymentEvent(**data)
        assert event.confidence_score == 0.75

        # Score en límite inferior
        data["confidence_score"] = 0.0
        event = NormalizedPaymentEvent(**data)
        assert event.confidence_score == 0.0

        # Score en límite superior
        data["confidence_score"] = 1.0
        event = NormalizedPaymentEvent(**data)
        assert event.confidence_score == 1.0

    def test_different_normalization_methods(self, valid_payment_data):
        """Verifica diferentes métodos de normalización"""
        methods = [
            NormalizationMethod.AI_BASED,
            NormalizationMethod.RULE_BASED,
            NormalizationMethod.HYBRID,
            NormalizationMethod.MANUAL,
            NormalizationMethod.FALLBACK,
        ]

        for method in methods:
            data = valid_payment_data.copy()
            data["normalization_method"] = method
            event = NormalizedPaymentEvent(**data)
            assert event.normalization_method == method

    def test_model_has_indexes(self):
        """Verifica que el modelo tenga índices definidos"""
        # En SQLModel, __table_args__ se procesa y los índices van a __table__
        # Verificar que el modelo tenga metadata de tabla
        assert hasattr(NormalizedPaymentEvent, "__table__")
        # Verificar que tenga índices
        if hasattr(NormalizedPaymentEvent, "__table__"):
            indexes = list(NormalizedPaymentEvent.__table__.indexes)
            assert len(indexes) > 0, "Model should have indexes defined"
