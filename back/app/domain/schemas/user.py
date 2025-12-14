"""
User schemas

DTOs for user management endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.user import Roles


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr = Field(..., description="User email")
    name: str = Field(..., min_length=1, max_length=100,
                      description="User name")


class UserCreate(UserBase):
    """User creation schema"""

    password: str = Field(..., min_length=8, description="User password")
    role: Roles = Field(default=Roles.CLIENT, description="User role")
    team_id: str | None = Field(
        None, max_length=100, description="Team name (only for DEVELOPER role)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "name": "John Doe",
                "password": "securepass123",
                "role": "CLIENT",
                "team_id": None,
            }
        }
    }


class UserUpdate(BaseModel):
    """User update schema"""

    email: EmailStr | None = Field(None, description="User email")
    name: str | None = Field(
        None, min_length=1, max_length=100, description="User name")
    password: str | None = Field(
        None, min_length=8, description="User password")
    role: Roles | None = Field(None, description="User role")
    team_id: str | None = Field(
        None, description="Team name (only for DEVELOPER/TEAM_LEADER roles)")
    is_active: bool | None = Field(None, description="Account status")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "John Updated",
                "is_active": True,
            }
        }
    }


class UserResponse(UserBase):
    """User response schema"""

    id: UUID = Field(..., description="User UUID")
    role: Roles = Field(..., description="User role")
    team_id: str | None = Field(None, description="Team name")
    is_active: bool = Field(..., description="Account status")
    created: datetime = Field(..., description="Creation timestamp")

    model_config = {"from_attributes": True}
