"""Tests unitarios para schemas de normalización"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain.models.enums import FailureReason, PaymentStatus
from app.domain.schemas.normalization_schemas import NormalizedPaymentSchema, RawEventInput


class TestNormalizedPaymentSchema:
    """Tests para NormalizedPaymentSchema"""

    @pytest.fixture
    def valid_payment_schema_data(self):
        """Datos válidos para crear un NormalizedPaymentSchema"""
        return {
            "merchant_name": "Acme Corp",
            "provider": "stripe",
            "country": "US",
            "status_category": PaymentStatus.APPROVED,
            "amount": Decimal("199.99"),
            "currency": "USD",
        }

    def test_create_schema_success(self, valid_payment_schema_data):
        """Verifica que se pueda crear un schema con datos válidos"""
        schema = NormalizedPaymentSchema(**valid_payment_schema_data)

        assert schema.merchant_name == "Acme Corp"
        assert schema.provider == "stripe"
        assert schema.country == "US"
        assert schema.status_category == PaymentStatus.APPROVED
        assert schema.amount == Decimal("199.99")
        assert schema.currency == "USD"

    def test_country_code_validation_uppercase(self, valid_payment_schema_data):
        """Verifica que el código de país se convierta a mayúsculas"""
        data = valid_payment_schema_data.copy()
        data["country"] = "mx"

        schema = NormalizedPaymentSchema(**data)
        assert schema.country == "MX"

    def test_country_code_validation_length(self, valid_payment_schema_data):
        """Verifica que el código de país deba tener 2 caracteres"""
        data = valid_payment_schema_data.copy()

        # Código de 1 carácter - debe fallar
        data["country"] = "U"
        with pytest.raises(ValidationError) as exc_info:
            NormalizedPaymentSchema(**data)
        # Pydantic valida min_length antes del validator
        assert "at least 2 characters" in str(exc_info.value)

        # Código de 3 caracteres - debe fallar
        data["country"] = "USA"
        with pytest.raises(ValidationError) as exc_info:
            NormalizedPaymentSchema(**data)
        assert "at most 2 characters" in str(exc_info.value)

    def test_amount_must_be_positive(self, valid_payment_schema_data):
        """Verifica que el monto deba ser positivo"""
        data = valid_payment_schema_data.copy()

        # Monto cero - debe fallar
        data["amount"] = Decimal("0")
        with pytest.raises(ValidationError) as exc_info:
            NormalizedPaymentSchema(**data)
        # Pydantic gt=0 validator
        assert "greater than 0" in str(exc_info.value)

        # Monto negativo - debe fallar
        data["amount"] = Decimal("-50.00")
        with pytest.raises(ValidationError) as exc_info:
            NormalizedPaymentSchema(**data)
        assert "greater than 0" in str(exc_info.value)

    def test_merchant_name_not_empty(self, valid_payment_schema_data):
        """Verifica que merchant_name no pueda estar vacío"""
        data = valid_payment_schema_data.copy()

        # String vacío
        data["merchant_name"] = ""
        with pytest.raises(ValidationError) as exc_info:
            NormalizedPaymentSchema(**data)
        # Pydantic min_length=1 validator
        assert "at least 1 character" in str(exc_info.value)

        # Solo espacios - pasa min_length pero falla custom validator
        data["merchant_name"] = "   "
        with pytest.raises(ValidationError) as exc_info:
            NormalizedPaymentSchema(**data)
        assert "Field cannot be empty" in str(exc_info.value)

    def test_provider_not_empty(self, valid_payment_schema_data):
        """Verifica que provider no pueda estar vacío"""
        data = valid_payment_schema_data.copy()

        data["provider"] = ""
        with pytest.raises(ValidationError) as exc_info:
            NormalizedPaymentSchema(**data)
        assert "at least 1 character" in str(exc_info.value)

    def test_strip_whitespace(self, valid_payment_schema_data):
        """Verifica que se eliminen espacios en blanco de merchant_name y provider"""
        data = valid_payment_schema_data.copy()
        data["merchant_name"] = "  Acme Corp  "
        data["provider"] = "  stripe  "

        schema = NormalizedPaymentSchema(**data)

        assert schema.merchant_name == "Acme Corp"
        assert schema.provider == "stripe"

    def test_latency_validation(self, valid_payment_schema_data):
        """Verifica que latency_ms deba ser razonable (< 5 minutos)"""
        data = valid_payment_schema_data.copy()

        # Latency válida
        data["latency_ms"] = 1500
        schema = NormalizedPaymentSchema(**data)
        assert schema.latency_ms == 1500

        # Latency muy alta (> 5 minutos) - debe fallar
        data["latency_ms"] = 400000
        with pytest.raises(ValidationError) as exc_info:
            NormalizedPaymentSchema(**data)
        assert "Latency seems unrealistic" in str(exc_info.value)

    def test_optional_fields(self, valid_payment_schema_data):
        """Verifica que los campos opcionales funcionen correctamente"""
        # Sin campos opcionales
        schema = NormalizedPaymentSchema(**valid_payment_schema_data)
        assert schema.failure_reason is None
        assert schema.provider_transaction_id is None
        assert schema.provider_status is None
        assert schema.latency_ms is None
        assert schema.event_metadata is None

        # Con campos opcionales
        data = valid_payment_schema_data.copy()
        data["failure_reason"] = FailureReason.CARD_DECLINED
        data["provider_transaction_id"] = "tx_123"
        data["provider_status"] = "succeeded"
        data["latency_ms"] = 150
        data["event_metadata"] = {"key": "value"}

        schema = NormalizedPaymentSchema(**data)
        assert schema.failure_reason == FailureReason.CARD_DECLINED
        assert schema.provider_transaction_id == "tx_123"
        assert schema.provider_status == "succeeded"
        assert schema.latency_ms == 150
        assert schema.event_metadata == {"key": "value"}

    def test_failed_payment_with_reason(self, valid_payment_schema_data):
        """Verifica un pago fallido con razón de fallo"""
        data = valid_payment_schema_data.copy()
        data["status_category"] = PaymentStatus.FAILED
        data["failure_reason"] = FailureReason.INSUFFICIENT_FUNDS

        schema = NormalizedPaymentSchema(**data)

        assert schema.status_category == PaymentStatus.FAILED
        assert schema.failure_reason == FailureReason.INSUFFICIENT_FUNDS


class TestRawEventInput:
    """Tests para RawEventInput"""

    def test_create_raw_event_input_success(self):
        """Verifica que se pueda crear un RawEventInput con datos válidos"""
        data = {
            "raw_event": {"status": "succeeded", "amount": 100},
            "provider": "stripe",
            "source": "webhook",
        }

        schema = RawEventInput(**data)

        assert schema.raw_event == {"status": "succeeded", "amount": 100}
        assert schema.provider == "stripe"
        assert schema.source == "webhook"

    def test_raw_event_cannot_be_empty(self):
        """Verifica que raw_event no pueda estar vacío"""
        data = {"raw_event": {}}

        with pytest.raises(ValidationError) as exc_info:
            RawEventInput(**data)
        # Pydantic min_length=1 para dict
        assert "at least 1 item" in str(exc_info.value)

    def test_optional_fields(self):
        """Verifica que provider y source sean opcionales"""
        data = {"raw_event": {"status": "succeeded"}}

        schema = RawEventInput(**data)

        assert schema.raw_event == {"status": "succeeded"}
        assert schema.provider is None
        assert schema.source is None

    def test_raw_event_with_complex_structure(self):
        """Verifica que raw_event acepte estructuras complejas"""
        data = {
            "raw_event": {
                "transaction": {"id": "tx_123", "amount": 100},
                "metadata": {"key": "value"},
                "nested": {"deep": {"structure": "ok"}},
            }
        }

        schema = RawEventInput(**data)

        assert schema.raw_event["transaction"]["id"] == "tx_123"
        assert schema.raw_event["nested"]["deep"]["structure"] == "ok"
