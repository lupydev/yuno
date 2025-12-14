"""
Custom exceptions for the notification system.
"""


class NotificationError(Exception):
    """Base exception for notification-related errors."""

    pass


class InvalidInteractionError(NotificationError):
    """Raised when an interaction payload is malformed or invalid."""

    pass


class MessageNotFoundError(NotificationError):
    """Raised when a message cannot be found for updating."""

    pass


class SlackAPIError(NotificationError):
    """Raised when Slack API returns an error."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        """
        Initialize SlackAPIError.

        Args:
            message: Error message
            error_code: Slack error code (e.g., 'channel_not_found')
        """
        super().__init__(message)
        self.error_code = error_code
