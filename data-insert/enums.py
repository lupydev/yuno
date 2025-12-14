"""Enumeraciones para el modelo de pagos normalizados"""

from enum import Enum


class PaymentStatus(str, Enum):
    """Estados normalizados de pago"""

    APPROVED = "approved"
    PENDING = "pending"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    UNPROCESSED = "unprocessed"


class FailureReason(str, Enum):
    """Razones específicas de fallo en pagos"""

    # Bank/Card Issues
    INSUFFICIENT_FUNDS = "insufficient_funds"
    CARD_DECLINED = "card_declined"
    EXPIRED_CARD = "expired_card"
    INVALID_CARD = "invalid_card"
    BANK_DECLINE = "bank_decline"

    # Security/Fraud
    FRAUD_SUSPECTED = "fraud_suspected"
    SECURITY_VIOLATION = "security_violation"
    BLOCKED_CARD = "blocked_card"

    # Technical Issues
    NETWORK_ERROR = "network_error"
    TIMEOUT = "timeout"
    PROVIDER_ERROR = "provider_error"
    SYSTEM_ERROR = "system_error"

    # Merchant/Configuration
    INVALID_MERCHANT = "invalid_merchant"
    MERCHANT_NOT_ACTIVE = "merchant_not_active"
    CONFIGURATION_ERROR = "configuration_error"

    # Transaction Issues
    DUPLICATE_TRANSACTION = "duplicate_transaction"
    AMOUNT_EXCEEDED = "amount_exceeded"
    INVALID_CURRENCY = "invalid_currency"

    # Unknown
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


class ErrorSource(str, Enum):
    """
    Identifica quién es responsable del error/fallo
    """

    PROVIDER = "provider"
    MERCHANT = "merchant"
    CUSTOMER = "customer"
    SYSTEM = "system"
    NETWORK = "network"
    UNKNOWN = "unknown"


class NormalizationMethod(str, Enum):
    """Método usado para normalizar el evento"""

    AI_BASED = "ai_based"
    RULE_BASED = "rule_based"
    HYBRID = "hybrid"
    MANUAL = "manual"
    FALLBACK = "fallback"
