"""
Unit tests for AIBasedNormalizer

Tests con mocking de LangChain/OpenAI para validar:
- Normalización exitosa
- Retry logic
- Timeout handling
- Rate limit handling
- Error handling
"""

from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from httpx import Request, Response
from openai import APIError, APITimeoutError, RateLimitError
from pydantic import ValidationError

from app.domain.exceptions import (
    AIServiceException,
    NormalizationException,
    NormalizationTimeoutException,
    RateLimitExceededException,
)
from app.domain.models.enums import (
    FailureReason,
    NormalizationMethod,
    PaymentStatus,
)
from app.domain.normalizers.ai_normalizer import AIBasedNormalizer
from app.infraestructure.ai.schemas import AIPaymentNormalizationOutput

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def create_mock_rate_limit_error():
    """Crea un RateLimitError mock válido"""
    mock_request = Request("POST", "https://api.openai.com/v1/chat/completions")
    mock_response = Response(429, request=mock_request)
    return RateLimitError(
        "Rate limit exceeded",
        response=mock_response,
        body={"error": {"message": "Rate limit exceeded"}},
    )


def create_mock_api_timeout_error():
    """Crea un APITimeoutError mock válido"""
    mock_request = Request("POST", "https://api.openai.com/v1/chat/completions")
    return APITimeoutError(request=mock_request)


def create_mock_api_error():
    """Crea un APIError mock válido"""
    mock_request = Request("POST", "https://api.openai.com/v1/chat/completions")
    # APIError necesita request y body
    return APIError("API error", request=mock_request, body=None)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def mock_langchain_client():
    """Mock de LangChainClient"""
    with patch("app.domain.normalizers.ai_normalizer.LangChainClient") as mock:
        yield mock


@pytest.fixture
def sample_raw_event():
    """Evento crudo de ejemplo"""
    return {
        "id": "pi_test_123",
        "amount": 5000,
        "currency": "usd",
        "status": "succeeded",
        "created": 1705315800,
        "metadata": {"merchant": "test_shop"},
    }


@pytest.fixture
def sample_ai_output():
    """Output de AI de ejemplo"""
    return AIPaymentNormalizationOutput(
        merchant_name="test_shop",
        provider="stripe",
        provider_transaction_id="pi_test_123",
        provider_status="succeeded",
        country="US",
        status_category=PaymentStatus.APPROVED,
        failure_reason=None,
        amount=Decimal("50.00"),
        currency="USD",
        latency_ms=None,
    )


# ============================================================================
# TESTS DE NORMALIZACIÓN EXITOSA
# ============================================================================


class TestAIBasedNormalizerSuccess:
    """Tests de casos exitosos"""

    def test_can_normalize_always_returns_true(self, mock_langchain_client):
        """AIBasedNormalizer puede normalizar cualquier evento"""
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm

        normalizer = AIBasedNormalizer()

        # Evento válido
        assert normalizer.can_normalize({"id": "test"}) is True

        # Evento extraño
        assert normalizer.can_normalize({"weird_field": "value"}) is True

        # Evento vacío
        assert normalizer.can_normalize({}) is True

    def test_normalize_success(self, mock_langchain_client, sample_raw_event, sample_ai_output):
        """Test normalización exitosa básica"""
        # Setup mock
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm
        mock_client_instance.invoke_with_logging.return_value = sample_ai_output

        # Execute
        normalizer = AIBasedNormalizer()
        result = normalizer.normalize(sample_raw_event)

        # Assert - Core fields
        assert result.merchant_name == "test_shop"
        assert result.provider == "stripe"
        assert result.provider_transaction_id == "pi_test_123"

        # Assert - Financial fields (currency preservation)
        assert result.amount == Decimal("50.00")
        assert result.currency == "USD"

        # Assert - Status
        assert result.status_category == PaymentStatus.APPROVED
        assert result.failure_reason is None

        # Assert - Normalization metadata
        assert result.normalization_method == NormalizationMethod.AI_BASED
        assert result.confidence_score == 0.95

        # Assert - Raw data preservation
        assert result.raw_data == sample_raw_event

        # Assert - Event metadata
        assert "normalization_timestamp" in result.event_metadata
        assert result.event_metadata["model_used"]
        assert result.event_metadata["prompt_version"] == "1.0.0"

    def test_normalize_with_failed_payment(self, mock_langchain_client, sample_raw_event):
        """Test normalización de pago fallido"""
        # Setup AI output para pago fallido
        failed_ai_output = AIPaymentNormalizationOutput(
            merchant_name="test_shop",
            provider="stripe",
            provider_transaction_id="pi_test_456",
            provider_status="failed",
            country="US",
            status_category=PaymentStatus.FAILED,
            failure_reason=FailureReason.INSUFFICIENT_FUNDS,
            amount=Decimal("100.00"),
            currency="USD",
            latency_ms=1500,
        )

        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm
        mock_client_instance.invoke_with_logging.return_value = failed_ai_output

        # Execute
        normalizer = AIBasedNormalizer()
        result = normalizer.normalize(sample_raw_event)

        # Assert
        assert result.status_category == PaymentStatus.FAILED
        assert result.failure_reason == FailureReason.INSUFFICIENT_FUNDS
        assert result.latency_ms == 1500

    def test_normalize_with_different_currencies(self, mock_langchain_client, sample_raw_event):
        """Test normalización con diferentes monedas"""
        currencies = [
            ("EUR", Decimal("250.00")),
            ("BRL", Decimal("500.00")),
            ("MXN", Decimal("1000.00")),
            ("GBP", Decimal("75.00")),
        ]

        for currency, amount in currencies:
            # Setup AI output
            ai_output = AIPaymentNormalizationOutput(
                merchant_name="test",
                provider="test",
                status_category=PaymentStatus.APPROVED,
                amount=amount,
                currency=currency,
            )

            mock_client_instance = Mock()
            mock_structured_llm = Mock()
            mock_langchain_client.return_value = mock_client_instance
            mock_client_instance.get_structured_llm.return_value = mock_structured_llm
            mock_client_instance.invoke_with_logging.return_value = ai_output

            # Execute
            normalizer = AIBasedNormalizer()
            result = normalizer.normalize(sample_raw_event)

            # Assert - Preserva currency original
            assert result.amount == amount
            assert result.currency == currency

    def test_normalize_with_lowercase_currency(self, mock_langchain_client, sample_raw_event):
        """Test que currency se convierte a uppercase"""
        ai_output = AIPaymentNormalizationOutput(
            merchant_name="test",
            provider="test",
            status_category=PaymentStatus.APPROVED,
            amount=Decimal("100.00"),
            currency="eur",  # lowercase
        )

        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm
        mock_client_instance.invoke_with_logging.return_value = ai_output

        normalizer = AIBasedNormalizer()
        result = normalizer.normalize(sample_raw_event)

        assert result.currency == "EUR"  # Convertido a uppercase

    def test_normalize_with_null_merchant_name(self, mock_langchain_client, sample_raw_event):
        """Test cuando merchant_name es None"""
        ai_output = AIPaymentNormalizationOutput(
            merchant_name=None,  # AI no pudo extraer merchant
            provider="stripe",
            status_category=PaymentStatus.APPROVED,
            amount=Decimal("100.00"),
            currency="USD",
        )

        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm
        mock_client_instance.invoke_with_logging.return_value = ai_output

        normalizer = AIBasedNormalizer()
        result = normalizer.normalize(sample_raw_event)

        assert result.merchant_name == "unknown_merchant"  # Fallback

    def test_normalize_with_null_country(self, mock_langchain_client, sample_raw_event):
        """Test cuando country es None"""
        ai_output = AIPaymentNormalizationOutput(
            merchant_name="test",
            provider="stripe",
            country=None,  # AI no pudo extraer country
            status_category=PaymentStatus.APPROVED,
            amount=Decimal("100.00"),
            currency="USD",
        )

        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm
        mock_client_instance.invoke_with_logging.return_value = ai_output

        normalizer = AIBasedNormalizer()
        result = normalizer.normalize(sample_raw_event)

        assert result.country == "XX"  # Default country code


# ============================================================================
# TESTS DE RETRY LOGIC
# ============================================================================


class TestAIBasedNormalizerRetry:
    """Tests de retry logic con Tenacity"""

    def test_normalize_retries_on_rate_limit(
        self, mock_langchain_client, sample_raw_event, sample_ai_output
    ):
        """Test retry en RateLimitError"""
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm

        # Primeros 2 intentos fallan con RateLimitError, tercero exitoso
        mock_client_instance.invoke_with_logging.side_effect = [
            create_mock_rate_limit_error(),
            create_mock_rate_limit_error(),
            sample_ai_output,  # Tercer intento exitoso
        ]

        normalizer = AIBasedNormalizer()
        result = normalizer.normalize(sample_raw_event)

        # Assert - normalización exitosa después de retries
        assert result.amount == Decimal("50.00")
        assert result.currency == "USD"

        # Assert - se llamó 3 veces
        assert mock_client_instance.invoke_with_logging.call_count == 3

    def test_normalize_retries_on_timeout(
        self, mock_langchain_client, sample_raw_event, sample_ai_output
    ):
        """Test retry en APITimeoutError"""
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm

        # Primeros 2 intentos timeout, tercero exitoso
        mock_client_instance.invoke_with_logging.side_effect = [
            create_mock_api_timeout_error(),
            create_mock_api_timeout_error(),
            sample_ai_output,
        ]

        normalizer = AIBasedNormalizer()
        result = normalizer.normalize(sample_raw_event)

        assert result.provider == "stripe"
        assert mock_client_instance.invoke_with_logging.call_count == 3

    def test_normalize_retries_on_api_error(
        self, mock_langchain_client, sample_raw_event, sample_ai_output
    ):
        """Test retry en APIError genérico"""
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm

        # Primer intento falla, segundo exitoso
        mock_client_instance.invoke_with_logging.side_effect = [
            create_mock_api_error(),
            sample_ai_output,
        ]

        normalizer = AIBasedNormalizer()
        result = normalizer.normalize(sample_raw_event)

        assert result.status_category == PaymentStatus.APPROVED
        assert mock_client_instance.invoke_with_logging.call_count == 2


# ============================================================================
# TESTS DE ERROR HANDLING
# ============================================================================


class TestAIBasedNormalizerErrors:
    """Tests de manejo de errores"""

    def test_normalize_raises_rate_limit_exception_after_retries(
        self, mock_langchain_client, sample_raw_event
    ):
        """Test que lanza RateLimitExceededException después de 3 retries"""
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm

        # Todos los intentos fallan con RateLimitError
        mock_client_instance.invoke_with_logging.side_effect = lambda *args, **kwargs: (
            _ for _ in ()
        ).throw(create_mock_rate_limit_error())

        normalizer = AIBasedNormalizer()

        with pytest.raises(RateLimitExceededException) as exc_info:
            normalizer.normalize(sample_raw_event)

        assert "rate limit exceeded" in str(exc_info.value).lower()
        # Debería haber intentado 3 veces
        assert mock_client_instance.invoke_with_logging.call_count == 3

    def test_normalize_raises_timeout_exception_after_retries(
        self, mock_langchain_client, sample_raw_event
    ):
        """Test que lanza NormalizationTimeoutException después de retries"""
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm

        mock_client_instance.invoke_with_logging.side_effect = lambda *args, **kwargs: (
            _ for _ in ()
        ).throw(create_mock_api_timeout_error())

        normalizer = AIBasedNormalizer()

        with pytest.raises(NormalizationTimeoutException) as exc_info:
            normalizer.normalize(sample_raw_event)

        assert "timed out" in str(exc_info.value).lower()
        assert mock_client_instance.invoke_with_logging.call_count == 3

    def test_normalize_raises_ai_service_exception_on_api_error(
        self, mock_langchain_client, sample_raw_event
    ):
        """Test que lanza AIServiceException en APIError persistente"""
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm

        # APIError persistente
        mock_client_instance.invoke_with_logging.side_effect = lambda *args, **kwargs: (
            _ for _ in ()
        ).throw(create_mock_api_error())

        normalizer = AIBasedNormalizer()

        with pytest.raises(AIServiceException) as exc_info:
            normalizer.normalize(sample_raw_event)

        assert "ai service error" in str(exc_info.value).lower()

    def test_normalize_raises_normalization_exception_on_validation_error(
        self, mock_langchain_client, sample_raw_event
    ):
        """Test que lanza NormalizationException en ValidationError"""
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm

        # Simular ValidationError (AI retornó schema inválido)
        mock_client_instance.invoke_with_logging.side_effect = ValidationError.from_exception_data(
            "test",
            [{"type": "missing", "loc": ("amount",), "msg": "Field required"}],
        )

        normalizer = AIBasedNormalizer()

        with pytest.raises(NormalizationException) as exc_info:
            normalizer.normalize(sample_raw_event)

        assert "validation failed" in str(exc_info.value).lower()

    def test_normalize_doesnt_retry_on_validation_error(
        self, mock_langchain_client, sample_raw_event
    ):
        """Test que NO reintenta en ValidationError (error permanente)"""
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm

        # ValidationError no debe generar retry
        mock_client_instance.invoke_with_logging.side_effect = ValidationError.from_exception_data(
            "test",
            [{"type": "missing", "loc": ("amount",), "msg": "Field required"}],
        )

        normalizer = AIBasedNormalizer()

        with pytest.raises(NormalizationException):
            normalizer.normalize(sample_raw_event)

        # Solo debe intentar 1 vez (ValidationError no es retriable)
        assert mock_client_instance.invoke_with_logging.call_count == 1


# ============================================================================
# TESTS DE METADATA Y LOGGING
# ============================================================================


class TestAIBasedNormalizerMetadata:
    """Tests de metadata y logging"""

    def test_normalize_includes_normalization_latency(
        self, mock_langchain_client, sample_raw_event, sample_ai_output
    ):
        """Test que calcula latency de normalización"""
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm
        mock_client_instance.invoke_with_logging.return_value = sample_ai_output

        normalizer = AIBasedNormalizer()
        result = normalizer.normalize(sample_raw_event)

        # Debe tener latency en metadata
        assert "normalization_latency_ms" in result.event_metadata
        assert isinstance(result.event_metadata["normalization_latency_ms"], int)
        assert result.event_metadata["normalization_latency_ms"] >= 0

    def test_normalize_includes_model_and_prompt_version(
        self, mock_langchain_client, sample_raw_event, sample_ai_output
    ):
        """Test que incluye model y prompt version en metadata"""
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm
        mock_client_instance.invoke_with_logging.return_value = sample_ai_output

        normalizer = AIBasedNormalizer()
        result = normalizer.normalize(sample_raw_event)

        assert "model_used" in result.event_metadata
        assert "prompt_version" in result.event_metadata
        assert result.event_metadata["prompt_version"] == "1.0.0"

    def test_normalize_includes_timestamp(
        self, mock_langchain_client, sample_raw_event, sample_ai_output
    ):
        """Test que incluye timestamp de normalización"""
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm
        mock_client_instance.invoke_with_logging.return_value = sample_ai_output

        normalizer = AIBasedNormalizer()
        result = normalizer.normalize(sample_raw_event)

        assert "normalization_timestamp" in result.event_metadata
        # Debe ser ISO format timestamp
        timestamp = result.event_metadata["normalization_timestamp"]
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO 8601 format

    def test_normalize_preserves_raw_data(
        self, mock_langchain_client, sample_raw_event, sample_ai_output
    ):
        """Test que preserva raw_data completo"""
        mock_client_instance = Mock()
        mock_structured_llm = Mock()
        mock_langchain_client.return_value = mock_client_instance
        mock_client_instance.get_structured_llm.return_value = mock_structured_llm
        mock_client_instance.invoke_with_logging.return_value = sample_ai_output

        normalizer = AIBasedNormalizer()
        result = normalizer.normalize(sample_raw_event)

        # Raw data debe ser idéntico al input
        assert result.raw_data == sample_raw_event
        assert result.raw_data["id"] == "pi_test_123"
        assert result.raw_data["metadata"]["merchant"] == "test_shop"


# ============================================================================
# TESTS DE INTEGRACIÓN (CON MOCK)
# ============================================================================


class TestAIBasedNormalizerIntegration:
    """Tests de integración básicos"""

    def test_initialization_with_custom_client(self):
        """Test inyección de dependencia de LangChainClient"""
        mock_client = Mock()
        mock_client.get_structured_llm.return_value = Mock()

        normalizer = AIBasedNormalizer(langchain_client=mock_client)
        assert normalizer._client == mock_client
