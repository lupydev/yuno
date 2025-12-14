"""
Domain schemas package

DTOs for API requests and responses.
"""

from app.domain.schemas.auth import LoginRequest, LoginResponse, TokenPayload, UserData
from app.domain.schemas.team import (
    DeveloperSummary,
    TeamCreate,
    TeamResponse,
    TeamWithDevelopers,
)
from app.domain.schemas.user import UserCreate, UserResponse, UserUpdate

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "TokenPayload",
    "UserData",
    "TeamCreate",
    "TeamResponse",
    "TeamWithDevelopers",
    "DeveloperSummary",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
]
