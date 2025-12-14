"""
Team service

Handles team management logic.
"""

from fastapi import HTTPException, status
from sqlmodel import select

from app.infraestructure.core.db import SessionDep
from app.models.team import Team
from app.models.user import Roles, User


class TeamService:
    @staticmethod
    def create_team(db: SessionDep, name: str) -> Team:
        """
        Create a new team

        Args:
            db: Database session
            name: Team name

        Returns:
            Created team

        Raises:
            HTTPException: If team name already exists
        """
        # Validate unique name
        existing = db.get(Team, name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Team name already exists",
            )

        team = Team(name=name)
        db.add(team)
        db.commit()
        db.refresh(team)
        return team

    @staticmethod
    def get_team(db: SessionDep, team_name: str) -> Team:
        """
        Get team by name

        Args:
            db: Database session
            team_name: Team name

        Returns:
            Team instance

        Raises:
            HTTPException: If team not found
        """
        team = db.get(Team, team_name)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Team not found",
            )
        return team

    @staticmethod
    def list_teams(db: SessionDep, skip: int = 0, limit: int = 100) -> list[Team]:
        """
        List all teams with pagination

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of teams
        """
        statement = select(Team).offset(skip).limit(limit)
        teams = db.exec(statement).all()
        return list(teams)

    @staticmethod
    def delete_team(db: SessionDep, team_name: str) -> None:
        """
        Delete a team

        Args:
            db: Database session
            team_name: Team name

        Raises:
            HTTPException: If team not found or has associated developers
        """
        team = TeamService.get_team(db, team_name)

        # Check if team has developers
        statement = select(User).where(User.team_id == team_name)
        developers = db.exec(statement).all()
        if developers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete team with {len(developers)} associated developer(s)",
            )

        db.delete(team)
        db.commit()

    @staticmethod
    def get_team_with_developers(db: SessionDep, team_name: str) -> Team:
        """
        Get team with its developers

        Args:
            db: Database session
            team_name: Team name

        Returns:
            Team with developers loaded

        Raises:
            HTTPException: If team not found
        """
        team = TeamService.get_team(db, team_name)
        # Force load developers relationship
        statement = select(User).where(
            User.team_id == team_name, User.role == Roles.DEVELOPER
        )
        team.developers = list(db.exec(statement).all())
        return team
