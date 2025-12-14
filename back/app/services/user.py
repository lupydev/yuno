"""
User service

Handles user management logic.
"""

"""
User service

Handles user management logic.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select

from app.infraestructure.core.db import SessionDep
from app.infraestructure.core.security import hash_password
from app.models.user import Roles, User
from sqlmodel import select

from app.infraestructure.core.db import SessionDep
from app.infraestructure.core.security import hash_password
from app.models.user import Roles, User


class UserService:
    @staticmethod
    def create_user(
        db: SessionDep,
        email: str,
        name: str,
        password: str,
        role: Roles = Roles.DEVELOPER,
        team_id: str | None = None,
    ) -> User:
        """
        Create a new user
        """
        Create a new user

        Args:
            db: Database session
            email: User email
            name: User name
            password: Plain password
            role: User role
            team_id: Team UUID (only for DEVELOPER role)
            db: Database session
            email: User email
            name: User name
            password: Plain password
            role: User role
            team_id: Team UUID (only for DEVELOPER role)

        Returns:
            Created user

        Raises:
            HTTPException: If email already exists or invalid team assignment
            Created user

        Raises:
            HTTPException: If email already exists or invalid team assignment
        """
        # Validate unique email
        existing = db.exec(select(User).where(User.email == email)).first()
        existing = db.exec(select(User).where(User.email == email)).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

        # Validate team assignment
        if team_id and role != Roles.DEVELOPER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only DEVELOPER role can be assigned to a team",
            )

        user = User(
            email=email,
            name=name,
            password=hash_password(password),
            role=role,
            team_id=team_id,
            email=email,
            name=name,
            password=hash_password(password),
            role=role,
            team_id=team_id,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user(db: SessionDep, user_id: UUID) -> User:
        """
        Get user by ID
    def get_user(db: SessionDep, user_id: UUID) -> User:
        """
        Get user by ID

        Args:
            db: Database session
            user_id: User UUID
            db: Database session
            user_id: User UUID

        Returns:
            User instance
            User instance

        Raises:
            HTTPException: If user not found
            HTTPException: If user not found
        """
        user = db.get(User, user_id)
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    @staticmethod
    def list_users(
        db: SessionDep,
        skip: int = 0,
        limit: int = 100,
        role: Roles | None = None,
    ) -> list[User]:
        """
        List all users with pagination and optional role filter
    def list_users(
        db: SessionDep,
        skip: int = 0,
        limit: int = 100,
        role: Roles | None = None,
    ) -> list[User]:
        """
        List all users with pagination and optional role filter

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Optional role filter

        Returns:
            List of users
        """
        statement = select(User)
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            role: Optional role filter

        Returns:
            List of users
        """
        statement = select(User)

        if role:
            statement = statement.where(User.role == role)
        if role:
            statement = statement.where(User.role == role)

        statement = statement.offset(skip).limit(limit)
        users = db.exec(statement).all()
        return list(users)
        statement = statement.offset(skip).limit(limit)
        users = db.exec(statement).all()
        return list(users)

    @staticmethod
    def update_user(
        db: SessionDep,
        user_id: UUID,
        email: str | None = None,
        name: str | None = None,
        password: str | None = None,
        role: Roles | None = None,
        team_id: str | None = None,
        is_active: bool | None = None,
        email: str | None = None,
        name: str | None = None,
        password: str | None = None,
        role: Roles | None = None,
        team_id: str | None = None,
        is_active: bool | None = None,
    ) -> User:
        """
        Update user information
        """
        Update user information

        Args:
            db: Database session
            user_id: User UUID
            email: New email
            name: New name
            password: New password
            role: New role
            team_id: New team UUID
            is_active: Account status
            db: Database session
            user_id: User UUID
            email: New email
            name: New name
            password: New password
            role: New role
            team_id: New team UUID
            is_active: Account status

        Returns:
            Updated user

        Raises:
            HTTPException: If user not found or validation fails
        """
        user = UserService.get_user(db, user_id)

        if email is not None:
            # Validate unique email
            existing = db.exec(select(User).where(User.email == email, User.id != user_id)).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists",
                )
            user.email = email

        if name is not None:
            user.name = name

        if password is not None:
            user.password = hash_password(password)

        if role is not None:
            user.role = role

        if team_id is not None:
            # Validate team assignment
            if role and role != Roles.DEVELOPER:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only DEVELOPER role can be assigned to a team",
                )
            user.team_id = team_id

        if is_active is not None:
            user.is_active = is_active

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: SessionDep, user_id: UUID) -> None:
        """
        Delete a user (soft delete by setting is_active to False)

        Args:
            db: Database session
            user_id: User UUID
            db: Database session
            user_id: User UUID

        Raises:
            HTTPException: If user not found
            HTTPException: If user not found
        """
        user = UserService.get_user(db, user_id)
        user.is_active = False
        db.add(user)
        db.commit()
