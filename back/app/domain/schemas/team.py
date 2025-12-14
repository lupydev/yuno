"""
Team schemas

DTOs for team management endpoints.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TeamBase(BaseModel):
    """Base team schema"""

    name: str = Field(..., min_length=1, max_length=100,
                      description="Team name")


class TeamCreate(TeamBase):
    """Team creation schema"""

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Backend Team",
            }
        }
    }


class TeamUpdate(BaseModel):
    """Team update schema"""

    name: str | None = Field(
        None, min_length=1, max_length=100, description="Team name")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Updated Team Name",
            }
        }
    }


class TeamResponse(TeamBase):
    """Team response schema"""

    created: datetime = Field(..., description="Creation timestamp")

    model_config = {"from_attributes": True}


class TeamWithDevelopers(TeamResponse):
    """Team with developers list"""

    developers: list["DeveloperSummary"] = Field(
        default_factory=list, description="Team developers")

    model_config = {"from_attributes": True}


class DeveloperSummary(BaseModel):
    """Developer summary for team listings"""

    id: UUID = Field(..., description="Developer UUID")
    name: str = Field(..., description="Developer name")
    email: str = Field(..., description="Developer email")

    model_config = {"from_attributes": True}
