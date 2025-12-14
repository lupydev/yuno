"""Tests unitarios para enumeraciones del dominio"""

from app.domain.models.enums import FailureReason, NormalizationMethod, PaymentStatus


class TestPaymentStatus:
    """Tests para PaymentStatus enum"""

    def test_all_statuses_exist(self):
        """Verifica que todos los estados esperados existan"""
        expected_statuses = {
            "APPROVED",
            "FAILED",
            "PENDING",
            "CANCELLED",
            "REFUNDED",
            "UNPROCESSED",
        }
        actual_statuses = {status.name for status in PaymentStatus}
        assert actual_statuses == expected_statuses

    def test_status_values(self):
        """Verifica que los valores sean lowercase snake_case"""
        assert PaymentStatus.APPROVED.value == "approved"
        assert PaymentStatus.FAILED.value == "failed"
        assert PaymentStatus.PENDING.value == "pending"
        assert PaymentStatus.CANCELLED.value == "cancelled"
        assert PaymentStatus.REFUNDED.value == "refunded"
        assert PaymentStatus.UNPROCESSED.value == "unprocessed"

    def test_status_is_string(self):
        """Verifica que PaymentStatus sea subclase de str"""
        assert isinstance(PaymentStatus.APPROVED, str)
        assert isinstance(PaymentStatus.FAILED, str)

    def test_status_equality(self):
        """Verifica comparación con strings"""
        assert PaymentStatus.APPROVED == "approved"
        assert PaymentStatus.FAILED == "failed"


class TestFailureReason:
    """Tests para FailureReason enum"""

    def test_bank_card_issues_exist(self):
        """Verifica que existan razones de fallo bancario/tarjeta"""
        bank_reasons = {
            FailureReason.INSUFFICIENT_FUNDS,
            FailureReason.CARD_DECLINED,
            FailureReason.EXPIRED_CARD,
            FailureReason.INVALID_CARD,
            FailureReason.BANK_DECLINE,
        }
        assert all(reason in FailureReason for reason in bank_reasons)

    def test_security_fraud_issues_exist(self):
        """Verifica que existan razones de seguridad/fraude"""
        security_reasons = {
            FailureReason.FRAUD_SUSPECTED,
            FailureReason.SECURITY_VIOLATION,
            FailureReason.BLOCKED_CARD,
        }
        assert all(reason in FailureReason for reason in security_reasons)

    def test_technical_issues_exist(self):
        """Verifica que existan razones técnicas"""
        technical_reasons = {
            FailureReason.NETWORK_ERROR,
            FailureReason.TIMEOUT,
            FailureReason.PROVIDER_ERROR,
            FailureReason.SYSTEM_ERROR,
        }
        assert all(reason in FailureReason for reason in technical_reasons)

    def test_failure_reason_values(self):
        """Verifica algunos valores específicos"""
        assert FailureReason.INSUFFICIENT_FUNDS.value == "insufficient_funds"
        assert FailureReason.FRAUD_SUSPECTED.value == "fraud_suspected"
        assert FailureReason.TIMEOUT.value == "timeout"
        assert FailureReason.UNKNOWN.value == "unknown"

    def test_failure_reason_is_string(self):
        """Verifica que FailureReason sea subclase de str"""
        assert isinstance(FailureReason.CARD_DECLINED, str)
        assert isinstance(FailureReason.TIMEOUT, str)


class TestNormalizationMethod:
    """Tests para NormalizationMethod enum"""

    def test_all_methods_exist(self):
        """Verifica que todos los métodos de normalización existan"""
        expected_methods = {
            "AI_BASED",
            "RULE_BASED",
            "HYBRID",
            "MANUAL",
            "FALLBACK",
        }
        actual_methods = {method.name for method in NormalizationMethod}
        assert actual_methods == expected_methods

    def test_method_values(self):
        """Verifica los valores de los métodos"""
        assert NormalizationMethod.AI_BASED.value == "ai_based"
        assert NormalizationMethod.RULE_BASED.value == "rule_based"
        assert NormalizationMethod.HYBRID.value == "hybrid"
        assert NormalizationMethod.MANUAL.value == "manual"
        assert NormalizationMethod.FALLBACK.value == "fallback"

    def test_method_is_string(self):
        """Verifica que NormalizationMethod sea subclase de str"""
        assert isinstance(NormalizationMethod.AI_BASED, str)
        assert isinstance(NormalizationMethod.HYBRID, str)
