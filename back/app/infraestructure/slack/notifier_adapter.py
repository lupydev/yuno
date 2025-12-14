"""
Slack Notifier Adapter - Infrastructure Implementation.

This module implements the NotifierPort interface for Slack, following
Hexagonal Architecture principles. It belongs to the Infrastructure layer
and handles all Slack-specific concerns.

Security Note:
    In production, you MUST validate Slack request signatures using the
    X-Slack-Signature and X-Slack-Request-Timestamp headers. See the
    TODO comments in the code for implementation guidance.

Design Principles Applied:
- Single Responsibility: Only handles Slack communication
- Dependency Injection: Receives configuration via constructor
- Open/Closed: Implements interface without modifying it
- Liskov Substitution: Can replace any NotifierPort implementation
"""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, Field

from app.domain.exceptions import InvalidInteractionError, NotificationError, SlackAPIError
from app.domain.interfaces.notifier_port import NotifierPort
from app.domain.models.alert import (
    AlertModel,
    AlertSeverity,
    InteractionResponse,
    InteractionUser,
    MessageID,
)

logger = logging.getLogger(__name__)


class SlackConfig(BaseModel):
    """Configuration for Slack integration."""

    bot_token: str = Field(..., description="Slack Bot Token (xoxb-...)")
    signing_secret: str = Field(...,
                                description="Slack Signing Secret for webhook validation")
    default_channel: str = Field(...,
                                 description="Default channel ID for alerts")
    timeout: int = Field(default=30, description="HTTP timeout in seconds")

    class Config:
        """Pydantic configuration."""

        frozen = True


class SlackNotifierAdapter(NotifierPort):
    """
    Slack implementation of the NotifierPort interface.

    This adapter translates domain operations into Slack API calls,
    using Block Kit for rich interactive messages.

    Attributes:
        _config: Slack configuration (tokens, channels, etc.)
        _client: Async HTTP client for Slack API calls
    """

    # Slack API endpoints
    _POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"
    _UPDATE_MESSAGE_URL = "https://slack.com/api/chat.update"

    # Block Kit action IDs (used to identify button clicks)
    _ACTION_ACKNOWLEDGE = "acknowledge_alert"

    def __init__(self, config: SlackConfig) -> None:
        """
        Initialize the Slack adapter.

        Args:
            config: Slack configuration including tokens and defaults
        """
        self._config = config
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(self._config.timeout),
            headers={
                "Authorization": f"Bearer {self._config.bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
        )

    async def __aenter__(self) -> "SlackNotifierAdapter":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit - cleanup resources."""
        await self._client.aclose()

    async def send_alert(self, alert: AlertModel) -> MessageID:
        """
        Send an alert to Slack using Block Kit with an acknowledgement button.

        The message includes:
        - Severity-based color coding
        - Rich text formatting with alert details
        - Interactive "Acknowledge" button (danger style for critical alerts)

        Args:
            alert: The alert to send

        Returns:
            MessageID: Unique identifier for the sent message

        Raises:
            SlackAPIError: If Slack API returns an error
            NotificationError: For network or unexpected errors
        """
        try:
            # Build the Block Kit message
            blocks = self._build_alert_blocks(alert)
            color = self._get_severity_color(alert.severity)

            payload = {
                "channel": self._config.default_channel,
                "text": f"🚨 {alert.title}",  # Fallback text for notifications
                "attachments": [
                    {
                        "color": color,
                        "blocks": blocks,
                    }
                ],
            }

            logger.info(
                f"Sending alert to Slack",
                extra={
                    "alert_id": str(alert.id),
                    "severity": alert.severity,
                    "channel": self._config.default_channel,
                },
            )

            response = await self._client.post(
                self._POST_MESSAGE_URL,
                json=payload,
            )

            response.raise_for_status()
            response_data = response.json()

            if not response_data.get("ok"):
                error_msg = response_data.get("error", "Unknown error")
                raise SlackAPIError(
                    f"Slack API error: {error_msg}",
                    error_code=error_msg,
                )

            message_id = MessageID(
                channel_id=response_data["channel"],
                timestamp=response_data["ts"],
            )

            logger.info(
                f"Alert sent successfully to Slack",
                extra={
                    "alert_id": str(alert.id),
                    "message_ts": message_id.timestamp,
                },
            )

            return message_id

        except httpx.HTTPError as e:
            logger.error(
                f"HTTP error sending alert to Slack: {e}", exc_info=True)
            raise NotificationError(f"Failed to send alert: {str(e)}") from e
        except Exception as e:
            logger.error(
                f"Unexpected error sending alert to Slack: {e}", exc_info=True)
            raise NotificationError(f"Unexpected error: {str(e)}") from e

    async def handle_interaction(self, payload: dict[str, Any]) -> InteractionResponse:
        """
        Process Slack interaction (button click) and update the message.

        Security Flow:
        1. TODO: Validate request signature (CRITICAL FOR PRODUCTION)
        2. Parse interaction payload
        3. Extract user and alert info
        4. Update message to show acknowledgement
        5. Return structured response

        The updated message removes the button and shows who acknowledged it.

        Args:
            payload: Raw Slack interaction payload

        Returns:
            InteractionResponse: Structured interaction data

        Raises:
            InvalidInteractionError: If payload is malformed
            NotificationError: If message update fails
        """
        try:
            # TODO: SECURITY - Validate Slack signature before processing
            # This is CRITICAL for production to prevent unauthorized requests
            # See: https://api.slack.com/authentication/verifying-requests-from-slack
            # Example implementation in _validate_slack_signature() below

            # Parse the interaction payload
            user_info = self._extract_user_info(payload)
            alert_id = self._extract_alert_id(payload)
            response_url = payload.get("response_url")

            if not response_url:
                raise InvalidInteractionError(
                    "Missing response_url in interaction payload")

            logger.info(
                f"Processing alert acknowledgement",
                extra={
                    "alert_id": str(alert_id),
                    "user_id": user_info.id,
                    "user_name": user_info.username,
                },
            )

            # Build the updated message (button removed, acknowledgement shown)
            acknowledged_at = datetime.utcnow()
            updated_blocks = self._build_acknowledged_blocks(
                alert_id=alert_id,
                user=user_info,
                acknowledged_at=acknowledged_at,
            )

            # Update the message using response_url (immediate response)
            # This is more reliable than chat.update for button interactions
            update_payload = {
                "replace_original": True,
                "blocks": updated_blocks,
            }

            response = await self._client.post(
                response_url,
                json=update_payload,
            )

            response.raise_for_status()

            logger.info(
                f"Alert acknowledged successfully",
                extra={
                    "alert_id": str(alert_id),
                    "user_id": user_info.id,
                },
            )

            return InteractionResponse(
                alert_id=alert_id,
                acknowledged_by=user_info,
                acknowledged_at=acknowledged_at,
                success=True,
                error_message=None,
            )

        except (InvalidInteractionError, SlackAPIError) as e:
            logger.warning(f"Invalid interaction or Slack error: {e}")
            raise
        except httpx.HTTPError as e:
            logger.error(
                f"HTTP error handling interaction: {e}", exc_info=True)
            raise NotificationError(
                f"Failed to update message: {str(e)}") from e
        except Exception as e:
            logger.error(
                f"Unexpected error handling interaction: {e}", exc_info=True)
            raise NotificationError(f"Unexpected error: {str(e)}") from e

    async def update_alert_status(
        self,
        message_id: MessageID,
        alert: AlertModel,
    ) -> None:
        """
        Update an existing Slack message with new alert status.

        Args:
            message_id: Identifier of the Slack message to update
            alert: Updated alert model

        Raises:
            SlackAPIError: If Slack API returns an error
            NotificationError: For network or unexpected errors
        """
        try:
            blocks = self._build_alert_blocks(alert)
            color = self._get_severity_color(alert.severity)

            payload = {
                "channel": message_id.channel_id,
                "ts": message_id.timestamp,
                "attachments": [
                    {
                        "color": color,
                        "blocks": blocks,
                    }
                ],
            }

            response = await self._client.post(
                self._UPDATE_MESSAGE_URL,
                json=payload,
            )

            response.raise_for_status()
            response_data = response.json()

            if not response_data.get("ok"):
                error_msg = response_data.get("error", "Unknown error")
                raise SlackAPIError(
                    f"Failed to update message: {error_msg}",
                    error_code=error_msg,
                )

            logger.info(
                f"Alert status updated in Slack",
                extra={
                    "alert_id": str(alert.id),
                    "new_status": alert.status,
                },
            )

        except httpx.HTTPError as e:
            logger.error(
                f"HTTP error updating alert status: {e}", exc_info=True)
            raise NotificationError(f"Failed to update alert: {str(e)}") from e
        except Exception as e:
            logger.error(
                f"Unexpected error updating alert status: {e}", exc_info=True)
            raise NotificationError(f"Unexpected error: {str(e)}") from e

    async def health_check(self) -> bool:
        """
        Check Slack API connectivity.

        Returns:
            bool: True if Slack is reachable, False otherwise
        """
        try:
            response = await self._client.post(
                "https://slack.com/api/auth.test",
                timeout=5.0,
            )
            response.raise_for_status()
            return response.json().get("ok", False)
        except Exception as e:
            logger.error(f"Slack health check failed: {e}")
            return False

    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------

    def _build_alert_blocks(self, alert: AlertModel) -> list[dict[str, Any]]:
        """
        Build Slack Block Kit blocks for an alert with acknowledgement button.

        Args:
            alert: The alert to format

        Returns:
            List of Block Kit blocks
        """
        severity_emoji = self._get_severity_emoji(alert.severity)

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{severity_emoji} {alert.title}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Message:*\n{alert.message}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Severity:*\n{alert.severity.upper()}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Source:*\n{alert.source}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{alert.status.upper()}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Created:*\n<!date^{int(alert.created_at.timestamp())}^{{date_short_pretty}} {{time}}|{alert.created_at.isoformat()}>",
                    },
                ],
            },
        ]

        # Add metadata if present
        if alert.metadata:
            metadata_text = "\n".join(
                f"• *{key}:* {value}" for key, value in alert.metadata.items()
            )
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Metadata:*\n{metadata_text}",
                    },
                }
            )

        blocks.append({"type": "divider"})

        # Add acknowledgement button (danger style for critical alerts)
        button_style = "danger" if alert.severity == AlertSeverity.CRITICAL else "primary"

        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 Acknowledge / Take Action",
                            "emoji": True,
                        },
                        "style": button_style,
                        "action_id": self._ACTION_ACKNOWLEDGE,
                        "value": str(alert.id),  # Alert ID in button value
                    }
                ],
            }
        )

        return blocks

    def _build_acknowledged_blocks(
        self,
        alert_id: UUID,
        user: InteractionUser,
        acknowledged_at: datetime,
    ) -> list[dict[str, Any]]:
        """
        Build Block Kit blocks showing the alert has been acknowledged.

        Removes the button and adds acknowledgement info.

        Args:
            alert_id: ID of the acknowledged alert
            user: User who acknowledged
            acknowledged_at: Timestamp of acknowledgement

        Returns:
            List of Block Kit blocks
        """
        formatted_time = acknowledged_at.strftime("%H:%M:%S")

        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🔒 *Acknowledged by <@{user.id}> at {formatted_time}*",
                },
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Alert ID: `{alert_id}` | Acknowledged at: <!date^{int(acknowledged_at.timestamp())}^{{date_short_pretty}} {{time}}|{acknowledged_at.isoformat()}>",
                    }
                ],
            },
        ]

    def _extract_user_info(self, payload: dict[str, Any]) -> InteractionUser:
        """
        Extract user information from Slack interaction payload.

        Args:
            payload: Slack interaction payload

        Returns:
            InteractionUser: User who triggered the interaction

        Raises:
            InvalidInteractionError: If user info is missing or malformed
        """
        user_data = payload.get("user", {})

        if not user_data or "id" not in user_data:
            raise InvalidInteractionError(
                "Missing user information in payload")

        return InteractionUser(
            id=user_data["id"],
            username=user_data.get(
                "username", user_data.get("name", "Unknown User")),
        )

    def _extract_alert_id(self, payload: dict[str, Any]) -> UUID:
        """
        Extract alert ID from Slack interaction payload.

        The alert ID is stored in the button's value field.

        Args:
            payload: Slack interaction payload

        Returns:
            UUID: Alert ID

        Raises:
            InvalidInteractionError: If alert ID is missing or invalid
        """
        try:
            actions = payload.get("actions", [])
            if not actions:
                raise InvalidInteractionError(
                    "No actions in interaction payload")

            # Get the first action (the button click)
            action = actions[0]
            alert_id_str = action.get("value")

            if not alert_id_str:
                raise InvalidInteractionError(
                    "Missing alert ID in action value")

            return UUID(alert_id_str)

        except (ValueError, KeyError) as e:
            raise InvalidInteractionError(
                f"Invalid alert ID format: {str(e)}") from e

    def _get_severity_color(self, severity: AlertSeverity) -> str:
        """
        Get Slack attachment color for severity level.

        Args:
            severity: Alert severity

        Returns:
            Hex color code
        """
        color_map = {
            AlertSeverity.CRITICAL: "#FF0000",  # Red
            AlertSeverity.HIGH: "#FF6B00",  # Orange
            AlertSeverity.MEDIUM: "#FFD700",  # Gold
            AlertSeverity.LOW: "#36A64F",  # Green
            AlertSeverity.INFO: "#439FE0",  # Blue
        }
        return color_map.get(severity, "#808080")  # Gray as default

    def _get_severity_emoji(self, severity: AlertSeverity) -> str:
        """
        Get emoji for severity level.

        Args:
            severity: Alert severity

        Returns:
            Emoji string
        """
        emoji_map = {
            AlertSeverity.CRITICAL: "🔴",
            AlertSeverity.HIGH: "🟠",
            AlertSeverity.MEDIUM: "🟡",
            AlertSeverity.LOW: "🟢",
            AlertSeverity.INFO: "🔵",
        }
        return emoji_map.get(severity, "⚪")

    # -------------------------------------------------------------------------
    # Security - Signature Validation (TODO: Implement for Production)
    # -------------------------------------------------------------------------

    def _validate_slack_signature(
        self,
        body: str,
        timestamp: str,
        signature: str,
    ) -> bool:
        """
        Validate Slack request signature to prevent unauthorized requests.

        TODO: CRITICAL FOR PRODUCTION
        This method should be called BEFORE processing any webhook from Slack.

        Implementation:
        1. Get timestamp from X-Slack-Request-Timestamp header
        2. Verify timestamp is within 5 minutes (prevent replay attacks)
        3. Compute HMAC SHA256 hash
        4. Compare with X-Slack-Signature header

        See: https://api.slack.com/authentication/verifying-requests-from-slack

        Args:
            body: Raw request body as string
            timestamp: X-Slack-Request-Timestamp header value
            signature: X-Slack-Signature header value

        Returns:
            bool: True if signature is valid

        Raises:
            InvalidInteractionError: If signature validation fails
        """
        # TODO: Implement signature validation
        # Example implementation:
        #
        # # Check timestamp to prevent replay attacks
        # current_timestamp = int(datetime.utcnow().timestamp())
        # if abs(current_timestamp - int(timestamp)) > 60 * 5:
        #     raise InvalidInteractionError("Request timestamp too old")
        #
        # # Compute expected signature
        # sig_basestring = f"v0:{timestamp}:{body}"
        # expected_signature = (
        #     "v0="
        #     + hmac.new(
        #         self._config.signing_secret.encode(),
        #         sig_basestring.encode(),
        #         hashlib.sha256,
        #     ).hexdigest()
        # )
        #
        # # Compare signatures (use constant-time comparison)
        # if not hmac.compare_digest(expected_signature, signature):
        #     raise InvalidInteractionError("Invalid request signature")
        #
        # return True

        logger.warning(
            "⚠️  Slack signature validation is NOT implemented. "
            "This is a SECURITY RISK in production!"
        )
        return True  # TODO: Remove this bypass in production
