"""Enumeraciones y catálogos para el dominio de pagos"""

from enum import Enum


class PaymentStatus(str, Enum):
    """Estado de la transacción de pago"""

    APPROVED = "approved"
    FAILED = "failed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    UNPROCESSED = "unprocessed"  # No se pudo normalizar


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
    NOT_APPLICABLE = "not_applicable"  # Para transacciones exitosas


class ErrorSource(str, Enum):
    """
    Identifica quién es responsable del error/fallo

    Usado para alertas inteligentes y análisis de root cause.
    """

    PROVIDER = "provider"  # Error del payment provider (timeout, gateway error, etc.)
    MERCHANT = "merchant"  # Error del merchant (config, credenciales, reglas de negocio)
    CUSTOMER = "customer"  # Error del cliente (tarjeta inválida, fondos insuficientes)
    SYSTEM = "system"  # Error interno del sistema (normalización, base de datos)
    NETWORK = "network"  # Error de red/conectividad
    UNKNOWN = "unknown"  # No se puede determinar el origen


class NormalizationMethod(str, Enum):
    """Método utilizado para normalizar el evento"""

    AI_BASED = "ai_based"  # Normalizado con IA (LangChain + OpenAI)
    RULE_BASED = "rule_based"  # Normalizado con reglas predefinidas
    HYBRID = "hybrid"  # Combinación de reglas + IA
    MANUAL = "manual"  # Normalizado manualmente
    FALLBACK = "fallback"  # Fallback cuando falla normalización
