"""Domain schemas package

DTOs for API requests and responses.
"""

from app.domain.schemas.api_schemas import (
    EventDetailResponse,
    EventIngestRequest,
    EventIngestResponse,
)
from app.domain.schemas.auth import LoginRequest, LoginResponse, TokenPayload, UserData
from app.domain.schemas.normalization_schemas import NormalizedPaymentSchema, RawEventInput
from app.domain.schemas.team import (
    DeveloperSummary,
    TeamCreate,
    TeamResponse,
    TeamWithDevelopers,
)
from app.domain.schemas.user import UserCreate, UserResponse, UserUpdate

__all__ = [
    # API Schemas
    "EventDetailResponse",
    "EventIngestRequest",
    "EventIngestResponse",
    # Auth Schemas
    "LoginRequest",
    "LoginResponse",
    "TokenPayload",
    "UserData",
    # Normalization Schemas
    "NormalizedPaymentSchema",
    "RawEventInput",
    # Team Schemas
    "DeveloperSummary",
    "TeamCreate",
    "TeamResponse",
    "TeamWithDevelopers",
    # User Schemas
    "UserCreate",
    "UserResponse",
    "UserUpdate",
]
