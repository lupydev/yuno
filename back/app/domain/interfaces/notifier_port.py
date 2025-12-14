"""
Notifier Port - Domain Interface.

This module defines the Port (interface) for the notification system following
Hexagonal Architecture principles. It belongs to the Domain layer and has no
infrastructure dependencies.

The Port defines the contract that any notification adapter must implement,
enabling dependency inversion and easy testing.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.domain.models.alert import AlertModel, InteractionResponse, MessageID


class NotifierPort(ABC):
    """
    Abstract base class defining the notification system contract.

    This is a Port in Hexagonal Architecture - it defines what the domain
    needs from the infrastructure layer without knowing how it's implemented.

    Implementations (Adapters) might include:
    - SlackNotifierAdapter
    - EmailNotifierAdapter
    - SMSNotifierAdapter
    - WebhookNotifierAdapter

    Design Principles Applied:
    - Interface Segregation Principle: Minimal, focused interface
    - Dependency Inversion Principle: Domain depends on abstraction
    - Open/Closed Principle: Extensible via new adapters
    """

    @abstractmethod
    async def send_alert(self, alert: AlertModel) -> MessageID:
        """
        Send a critical alert through the notification channel.

        This method should:
        1. Format the alert for the target platform
        2. Include interactive elements (e.g., acknowledgement button)
        3. Send the message asynchronously
        4. Return a unique identifier for the sent message

        Args:
            alert: The alert model containing all notification data

        Returns:
            MessageID: Unique identifier for the sent message, used for updates

        Raises:
            NotificationError: If the notification fails to send
            ValidationError: If the alert data is invalid
        """
        ...

    @abstractmethod
    async def handle_interaction(self, payload: dict[str, Any]) -> InteractionResponse:
        """
        Process user interaction with a notification (e.g., button click).

        This method should:
        1. Validate the interaction payload
        2. Extract user and alert information
        3. Update the original message to reflect acknowledgement
        4. Return structured interaction data

        Args:
            payload: Raw interaction payload from the notification platform
                    (e.g., Slack interaction payload)

        Returns:
            InteractionResponse: Structured data about the interaction

        Raises:
            InvalidInteractionError: If the payload is malformed or invalid
            NotificationError: If updating the message fails
        """
        ...

    @abstractmethod
    async def update_alert_status(
        self,
        message_id: MessageID,
        alert: AlertModel,
    ) -> None:
        """
        Update an existing alert message with new status information.

        This method should:
        1. Locate the original message using the MessageID
        2. Update the message content to reflect the new alert status
        3. Maintain visual consistency with the original message

        Args:
            message_id: Identifier of the message to update
            alert: Updated alert model with new status

        Raises:
            NotificationError: If the update fails
            MessageNotFoundError: If the message cannot be located
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the notification service is healthy and reachable.

        Returns:
            bool: True if the service is healthy, False otherwise
        """
        ...
