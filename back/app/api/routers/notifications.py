"""
Notifications Router - FastAPI Integration Example.

This module demonstrates how to integrate the NotifierPort with FastAPI,
showing proper dependency injection and error handling.

Endpoints:
- POST /api/notifications/alert - Send a new alert
- POST /api/notifications/slack/interactions - Handle Slack button clicks
"""

import json
import logging
from typing import Annotated, AsyncGenerator

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Request, status

from app.domain.exceptions import InvalidInteractionError, NotificationError
from app.domain.interfaces.notifier_port import NotifierPort
from app.domain.models.alert import AlertModel, AlertSeverity, InteractionResponse, MessageID
from app.infraestructure.core.config import settings
from app.infraestructure.slack import SlackConfig, SlackNotifierAdapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# -------------------------------------------------------------------------
# Dependency Injection
# -------------------------------------------------------------------------


async def get_slack_notifier() -> AsyncGenerator[NotifierPort, None]:
    """
    Dependency that provides a configured Slack notifier.

    This demonstrates the Dependency Inversion Principle:
    - The route depends on NotifierPort (abstraction)
    - We inject SlackNotifierAdapter (concrete implementation)
    - Easy to swap for EmailNotifierAdapter, MockNotifierAdapter, etc.

    In production, you might want to:
    - Cache the adapter instance
    - Use a factory pattern for multiple notifier types
    - Load configuration from environment/database
    """
    config = SlackConfig(
        bot_token=settings.SLACK_BOT_TOKEN,
        signing_secret=settings.SLACK_SIGNING_SECRET,
        default_channel=settings.SLACK_ALERTS_CHANNEL,
        timeout=30,
    )

    # Note: In production, you might want to manage the adapter lifecycle
    # differently (e.g., singleton, connection pooling, etc.)
    adapter = SlackNotifierAdapter(config=config)

    try:
        yield adapter
    finally:
        # Cleanup resources
        await adapter._client.aclose()


# -------------------------------------------------------------------------
# Route Handlers
# -------------------------------------------------------------------------


@router.post(
    "/alert",
    response_model=MessageID,
    status_code=status.HTTP_201_CREATED,
    summary="Send Critical Alert",
    description="Send a critical alert notification with interactive acknowledgement button",
)
async def send_alert(
    alert: AlertModel,
    notifier: Annotated[NotifierPort, Depends(get_slack_notifier)],
) -> MessageID:
    """
    Send a critical alert to the configured notification channel.

    The alert will include:
    - Rich formatted message with severity, source, and metadata
    - Interactive acknowledgement button
    - Color-coded based on severity

    Args:
        alert: Alert data to send
        notifier: Injected notifier implementation

    Returns:
        MessageID: Unique identifier for the sent message

    Raises:
        HTTPException: If sending fails
    """
    try:
        logger.info(
            f"Sending alert notification",
            extra={
                "alert_id": str(alert.id),
                "severity": alert.severity,
                "source": alert.source,
            },
        )

        message_id = await notifier.send_alert(alert)

        logger.info(
            f"Alert notification sent successfully",
            extra={
                "alert_id": str(alert.id),
                "message_ts": message_id.timestamp,
            },
        )

        return message_id

    except NotificationError as e:
        logger.error(f"Failed to send alert notification: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to send notification: {str(e)}",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error sending alert: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.post(
    "/slack/interactions",
    response_model=InteractionResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle Slack Interactions",
    description="Webhook endpoint for Slack interactive messages (button clicks)",
)
async def handle_slack_interaction(
    request: Request,
    notifier: Annotated[NotifierPort, Depends(get_slack_notifier)],
    x_slack_signature: Annotated[str | None, Header()] = None,
    x_slack_request_timestamp: Annotated[str | None, Header()] = None,
) -> InteractionResponse:
    """
    Handle Slack interaction webhooks (button clicks, menu selections, etc.).

    This endpoint:
    1. Receives the Slack interaction payload
    2. TODO: Validates the request signature (CRITICAL for production)
    3. Processes the interaction (e.g., acknowledgement)
    4. Updates the original message
    5. Returns structured response data

    Security:
        In production, you MUST validate the Slack signature before processing.
        See the adapter's _validate_slack_signature method.

    Args:
        request: FastAPI request object
        notifier: Injected notifier implementation
        x_slack_signature: Slack signature header (for validation)
        x_slack_request_timestamp: Slack timestamp header (for validation)

    Returns:
        InteractionResponse: Details about the processed interaction

    Raises:
        HTTPException: If interaction processing fails
    """
    try:
        # Parse the Slack payload
        # Slack sends interactions as form-encoded with a "payload" field
        form_data = await request.form()
        payload_str = form_data.get("payload")

        if not payload_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing payload in request",
            )

        payload = json.loads(payload_str)

        # TODO: CRITICAL - Validate Slack signature before processing
        # In production, call notifier._validate_slack_signature() here
        # Example:
        # if x_slack_signature and x_slack_request_timestamp:
        #     body = await request.body()
        #     notifier._validate_slack_signature(
        #         body=body.decode(),
        #         timestamp=x_slack_request_timestamp,
        #         signature=x_slack_signature,
        #     )
        # else:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="Missing security headers",
        #     )

        logger.info(
            "Processing Slack interaction",
            extra={
                "action_type": payload.get("type"),
                "user_id": payload.get("user", {}).get("id"),
            },
        )

        # Process the interaction through the notifier
        response = await notifier.handle_interaction(payload)

        logger.info(
            "Slack interaction processed successfully",
            extra={
                "alert_id": str(response.alert_id),
                "acknowledged_by": response.acknowledged_by.username,
            },
        )

        return response

    except InvalidInteractionError as e:
        logger.warning(f"Invalid Slack interaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid interaction: {str(e)}",
        ) from e
    except NotificationError as e:
        logger.error(
            f"Failed to process Slack interaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to process interaction: {str(e)}",
        ) from e
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Slack payload: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error handling Slack interaction: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from e


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Notification Health Check",
)
async def health_check(
    notifier: Annotated[NotifierPort, Depends(get_slack_notifier)],
) -> dict[str, bool]:
    """
    Check if the notification service is healthy.

    Returns:
        dict: Health status
    """
    is_healthy = await notifier.health_check()

    if not is_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notification service is unhealthy",
        )

    return {"healthy": True}
