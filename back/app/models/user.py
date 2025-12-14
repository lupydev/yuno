"""
User domain model

Represents authenticated users in the system.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.team import Team


# TODO: move to enums
class Roles(str, Enum):
    """User role enumeration"""

    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"


class User(SQLModel, table=True):
    """
    User model - Authenticated user entity

    Attributes:
        id: Unique identifier
        email: User email (unique)
        name: User's name
        password: User password (hashed)
        role: User role (ADMIN | DEVELOPER)
        team_id: Team reference (only for DEVELOPER role)
        is_active: Account status
        created: Account creation timestamp
    """

    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, max_length=255)
    name: str = Field(max_length=100)
    password: str = Field(max_length=255)
    role: Roles = Field(default=Roles.DEVELOPER)
    team_id: str | None = Field(default=None, foreign_key="teams.name", max_length=100)
    is_active: bool = Field(default=True)
    created: datetime = Field(default_factory=datetime.now)

    # Relationships
    team: Optional["Team"] = Relationship(back_populates="developers")
