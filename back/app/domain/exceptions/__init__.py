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

# Import notification exceptions from exceptions.py module
try:
    from ..exceptions import (
        InvalidInteractionError,
        MessageNotFoundError,
        NotificationError,
        SlackAPIError,
    )
except ImportError:
    # If not in exceptions submodule, try parent level
    try:
        import sys
        from pathlib import Path

        parent_dir = Path(__file__).parent.parent
        sys.path.insert(0, str(parent_dir))
        from exceptions import (
            InvalidInteractionError,
            MessageNotFoundError,
            NotificationError,
            SlackAPIError,
        )
    except ImportError:
        # Define dummy classes if not found
        class NotificationError(Exception):
            pass

        class InvalidInteractionError(NotificationError):
            pass

        class MessageNotFoundError(NotificationError):
            pass

        class SlackAPIError(NotificationError):
            pass


__all__ = [
    "PaymentObservabilityException",
    "NormalizationException",
    "AIServiceException",
    "RateLimitExceededException",
    "NormalizationTimeoutException",
    "ValidationException",
    "RepositoryException",
    "NotificationError",
    "InvalidInteractionError",
    "MessageNotFoundError",
    "SlackAPIError",
]
