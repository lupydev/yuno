"""
Team domain model

Represents developer teams in the system.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.user import User


class Team(SQLModel, table=True):
    """
    Team model - Developer team entity

    Attributes:
        name: Team name (primary key)
        created: Team creation timestamp
    """

    __tablename__ = "teams"

    name: str = Field(primary_key=True, max_length=100)
    created: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships
    developers: list["User"] = Relationship(back_populates="team")
