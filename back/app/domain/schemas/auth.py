"""
Authentication schemas

DTOs for authentication endpoints.
"""

from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request schema"""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "admin@yknow.com",
                "password": "securepassword123",
            }
        }
    }


class UserData(BaseModel):
    """User data response schema"""

    id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="User name")
    role: str = Field(...,
                      description="User role (ADMIN | DEVELOPER | CLIENT)")
    team_id: str | None = Field(
        None, description="Team name (only for DEVELOPER role)")

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """Login response schema"""

    token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    user_data: UserData = Field(..., description="Authenticated user data")

    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "user_data": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "admin@yknow.com",
                    "name": "John Doe",
                    "role": "ADMIN",
                    "team_id": None,
                },
            }
        }
    }


class TokenPayload(BaseModel):
    """JWT token payload schema"""

    sub: str = Field(..., description="Subject (user ID)")
    exp: int = Field(..., description="Expiration timestamp")
    type: str | None = Field(None, description="Token type")
