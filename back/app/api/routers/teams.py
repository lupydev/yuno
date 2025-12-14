"""
Team management router

API endpoints for team CRUD operations.
"""

from fastapi import APIRouter, status

from app.domain.schemas.team import (
    TeamCreate,
    TeamResponse,
    TeamUpdate,
    TeamWithDevelopers,
)
from app.infraestructure.core.db import SessionDep
from app.services.team import TeamService

router = APIRouter()


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(data: TeamCreate, db: SessionDep):
    """Create a new team"""
    return TeamService.create_team(db, data.name)


@router.get("/", response_model=list[TeamResponse])
def list_teams(db: SessionDep, skip: int = 0, limit: int = 100):
    """List all teams"""
    return TeamService.list_teams(db, skip, limit)


@router.get("/names/all", response_model=list[str])
def get_team_names(db: SessionDep):
    """Get all team names"""
    return TeamService.get_team_names(db)


@router.get("/{team_name}", response_model=TeamWithDevelopers)
def get_team(team_name: str, db: SessionDep):
    """Get team by name with developers"""
    return TeamService.get_team_with_developers(db, team_name)


@router.patch("/{team_name}", response_model=TeamResponse)
def update_team(team_name: str, data: TeamUpdate, db: SessionDep):
    """Update team name"""
    return TeamService.update_team(db, team_name, data.name)


@router.delete("/{team_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_team(team_name: str, db: SessionDep):
    """Delete a team"""
    TeamService.delete_team(db, team_name)
