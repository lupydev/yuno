"""
Domain models for the Notification system.

This module defines the core domain models for alerts and notification interactions,
following Clean Architecture principles and strict typing.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class AlertSeverity(str, Enum):
    """Severity levels for alerts."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    """Status of an alert."""

    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class AlertModel(BaseModel):
    """
    Domain model representing a critical alert.

    This is a pure domain model with no infrastructure concerns.
    """

    id: UUID = Field(default_factory=uuid4,
                     description="Unique identifier for the alert")
    title: str = Field(..., min_length=1, max_length=200,
                       description="Alert title")
    message: str = Field(..., min_length=1, max_length=4000,
                         description="Alert message body")
    severity: AlertSeverity = Field(
        default=AlertSeverity.MEDIUM, description="Severity level")
    status: AlertStatus = Field(
        default=AlertStatus.PENDING, description="Current status")
    source: str = Field(..., min_length=1, max_length=100,
                        description="Source system/service")
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Additional context")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp")

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: dict[str, str]) -> dict[str, str]:
        """Ensure metadata values are strings."""
        if not all(isinstance(key, str) and isinstance(value, str) for key, value in v.items()):
            raise ValueError(
                "Metadata must contain only string keys and values")
        return v

    class Config:
        """Pydantic configuration."""

        frozen = False  # Allow status updates
        use_enum_values = True


class MessageID(BaseModel):
    """
    Value object representing a message identifier from the notification system.
    """

    channel_id: str = Field(..., description="Channel or conversation ID")
    timestamp: str = Field(...,
                           description="Message timestamp (unique ID in Slack)")

    class Config:
        """Pydantic configuration."""

        frozen = True  # Immutable value object


class InteractionUser(BaseModel):
    """Represents a user who interacted with a notification."""

    id: str = Field(..., description="User ID from the notification platform")
    username: str = Field(..., description="Username or display name")

    class Config:
        """Pydantic configuration."""

        frozen = True


class InteractionResponse(BaseModel):
    """
    Response after handling an interaction (e.g., button click).

    This model encapsulates what happened when a user acknowledged an alert.
    """

    alert_id: UUID = Field(...,
                           description="ID of the alert that was acknowledged")
    acknowledged_by: InteractionUser = Field(...,
                                             description="User who acknowledged")
    acknowledged_at: datetime = Field(
        default_factory=datetime.utcnow, description="Acknowledgement time")
    success: bool = Field(...,
                          description="Whether the interaction was processed successfully")
    error_message: Optional[str] = Field(
        default=None, description="Error message if unsuccessful")

    class Config:
        """Pydantic configuration."""

        frozen = True
