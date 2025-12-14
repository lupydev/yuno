"""
Domain Exceptions Module

Re-exporta todas las excepciones para mantener API público limpio.
"""

from .exceptions import (
    AIServiceException,
    NormalizationException,
    NormalizationTimeoutException,
    PaymentObservabilityException,
    RateLimitExceededException,
    RepositoryException,
    ValidationException,
)

__all__ = [
    "PaymentObservabilityException",
    "NormalizationException",
    "AIServiceException",
    "RateLimitExceededException",
    "NormalizationTimeoutException",
    "ValidationException",
    "RepositoryException",
]
