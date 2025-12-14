"""
Unit tests for domain exceptions

Tests para validar la jerarquía de excepciones y su comportamiento
"""

import pytest

from app.domain.exceptions import (
    AIServiceException,
    NormalizationException,
    NormalizationTimeoutException,
    PaymentObservabilityException,
    RateLimitExceededException,
)


class TestPaymentObservabilityException:
    """Tests para excepción base"""

    def test_basic_exception(self):
        """Debe crear excepción básica"""
        exc = PaymentObservabilityException("Test error")

        assert str(exc) == "Test error"
        assert isinstance(exc, Exception)

    def test_exception_with_error_code(self):
        """Debe soportar error_code"""
        exc = PaymentObservabilityException("Error", error_code="E001")

        assert str(exc) == "Error"
        assert exc.error_code == "E001"

    def test_exception_inheritance(self):
        """Debe ser instancia de Exception"""
        exc = PaymentObservabilityException("Test")

        assert isinstance(exc, Exception)


class TestNormalizationException:
    """Tests para excepción de normalización"""

    def test_basic_normalization_exception(self):
        """Debe crear excepción de normalización"""
        exc = NormalizationException("Normalization failed")

        assert str(exc) == "Normalization failed"
        assert isinstance(exc, PaymentObservabilityException)


class TestAIServiceException:
    """Tests para excepción de AI Service"""

    def test_basic_ai_exception(self):
        """Debe crear excepción de AI Service"""
        exc = AIServiceException("AI service unavailable")

        assert str(exc) == "AI service unavailable"
        assert isinstance(exc, NormalizationException)
        assert isinstance(exc, PaymentObservabilityException)


class TestRateLimitExceededException:
    """Tests para excepción de rate limit"""

    def test_rate_limit_with_retry_after(self):
        """Debe incluir retry_after"""
        exc = RateLimitExceededException("Rate limit exceeded", retry_after=60)

        assert str(exc) == "Rate limit exceeded"
        assert exc.retry_after == 60
        assert isinstance(exc, AIServiceException)

    def test_rate_limit_without_retry_after(self):
        """Debe funcionar sin retry_after"""
        exc = RateLimitExceededException("Rate limit exceeded")

        assert exc.retry_after is None

    def test_rate_limit_inheritance(self):
        """Debe heredar correctamente la jerarquía"""
        exc = RateLimitExceededException("Test", retry_after=30)

        assert isinstance(exc, AIServiceException)
        assert isinstance(exc, NormalizationException)
        assert isinstance(exc, PaymentObservabilityException)
        assert isinstance(exc, Exception)


class TestNormalizationTimeoutException:
    """Tests para excepción de timeout"""

    def test_timeout_with_timeout_seconds(self):
        """Debe incluir timeout_seconds"""
        exc = NormalizationTimeoutException("Timeout occurred", timeout_seconds=10)

        assert str(exc) == "Timeout occurred"
        assert exc.timeout_seconds == 10
        assert isinstance(exc, AIServiceException)

    def test_timeout_without_timeout_seconds(self):
        """Debe funcionar sin timeout_seconds"""
        exc = NormalizationTimeoutException("Timeout")

        assert exc.timeout_seconds is None

    def test_timeout_inheritance(self):
        """Debe heredar correctamente la jerarquía"""
        exc = NormalizationTimeoutException("Test", timeout_seconds=5)

        assert isinstance(exc, AIServiceException)
        assert isinstance(exc, NormalizationException)
        assert isinstance(exc, PaymentObservabilityException)


class TestExceptionHierarchy:
    """Tests para verificar la jerarquía de excepciones"""

    def test_all_exceptions_inherit_from_base(self):
        """Todas las excepciones deben heredar de PaymentObservabilityException"""
        exceptions = [
            NormalizationException("test"),
            AIServiceException("test"),
            RateLimitExceededException("test"),
            NormalizationTimeoutException("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, PaymentObservabilityException)
            assert isinstance(exc, Exception)

    def test_ai_exceptions_inherit_from_normalization(self):
        """Excepciones de AI deben heredar de NormalizationException"""
        exceptions = [
            AIServiceException("test"),
            RateLimitExceededException("test"),
            NormalizationTimeoutException("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, NormalizationException)

    def test_specific_exceptions_inherit_from_ai_service(self):
        """Excepciones específicas deben heredar de AIServiceException"""
        exceptions = [
            RateLimitExceededException("test"),
            NormalizationTimeoutException("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, AIServiceException)


class TestExceptionCatching:
    """Tests para verificar que se puedan capturar correctamente"""

    def test_catch_specific_exception(self):
        """Debe poder capturar excepción específica"""
        with pytest.raises(RateLimitExceededException):
            raise RateLimitExceededException("Test", retry_after=60)

    def test_catch_parent_exception(self):
        """Debe poder capturar con excepción padre"""
        with pytest.raises(AIServiceException):
            raise RateLimitExceededException("Test", retry_after=60)

        with pytest.raises(NormalizationException):
            raise RateLimitExceededException("Test", retry_after=60)

    def test_catch_base_exception(self):
        """Debe poder capturar con excepción base"""
        with pytest.raises(PaymentObservabilityException):
            raise RateLimitExceededException("Test", retry_after=60)

    def test_exception_message_preserved(self):
        """El mensaje debe preservarse a través de la jerarquía"""
        message = "Specific error message"

        with pytest.raises(RateLimitExceededException) as exc_info:
            raise RateLimitExceededException(message, retry_after=30)

        assert str(exc_info.value) == message
        assert exc_info.value.retry_after == 30
