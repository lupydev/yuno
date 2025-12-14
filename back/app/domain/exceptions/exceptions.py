"""
Domain Exceptions

Jerarquía de excepciones custom para el dominio de pagos.
Siguiendo Best Practice: usar jerarquía específica en vez de Exception genérico.
"""


class PaymentObservabilityException(Exception):
    """
    Base exception para el dominio de observabilidad de pagos

    Todas las excepciones del dominio heredan de esta clase.
    Permite catch específico y manejo diferenciado.
    """

    def __init__(self, message: str, error_code: str | None = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class NormalizationException(PaymentObservabilityException):
    """
    Errores durante el proceso de normalización de eventos

    Usado cuando no se puede normalizar un evento por cualquier razón
    (validación, formato, datos faltantes, etc.)
    """

    pass


class AIServiceException(NormalizationException):
    """
    Errores específicos de servicios de IA (OpenAI, LangChain)

    Ejemplos:
    - Timeouts de API
    - Rate limits excedidos
    - Errores de parsing de respuesta
    - Model not available
    """

    pass


class RateLimitExceededException(AIServiceException):
    """
    Rate limit de OpenAI excedido

    Contiene información sobre cuándo reintentar (Retry-After header)
    """

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message, error_code="RATE_LIMIT_EXCEEDED")
        self.retry_after = retry_after


class NormalizationTimeoutException(AIServiceException):
    """
    Timeout durante normalización con IA

    Puede indicar que el evento es muy complejo o el servicio está lento
    """

    def __init__(self, message: str, timeout_seconds: int | None = None):
        super().__init__(message, error_code="NORMALIZATION_TIMEOUT")
        self.timeout_seconds = timeout_seconds


class ValidationException(PaymentObservabilityException):
    """
    Errores de validación de negocio

    Usado cuando los datos no cumplen reglas de negocio
    (amounts negativos, country codes inválidos, etc.)
    """

    pass


class RepositoryException(PaymentObservabilityException):
    """
    Errores de persistencia y acceso a datos

    Ejemplos:
    - Connection errors
    - Constraint violations
    - Transacciones fallidas
    """

    pass
