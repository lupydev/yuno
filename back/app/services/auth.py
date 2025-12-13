"""
Authentication service

Handles user authentication logic.
"""

from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlmodel import select

from app.core.db import SessionDep
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models import User


class AuthService:
    @staticmethod
    def authenticate_user(db: SessionDep, email: EmailStr, password: str) -> User:
        """
        Authenticate user with email and password

        Args:
            db: Database session
            email: User email
            password: Plain password

        Returns:
            Authenticated user

        Raises:
            HTTPException: If credentials are invalid or account is inactive
        """
        # Find user by email
        statement = select(User).where(User.email == email)
        user = db.exec(statement).first()

        # Validate credentials
        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check if account is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive",
            )

        return user

    @staticmethod
    def generate_tokens(user_id: str) -> dict[str, str]:
        """
        Generate access and refresh tokens for user

        Args:
            user_id: User ID string

        Returns:
            Dictionary with access_token and refresh_token
        """
        token_data = {"sub": user_id}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
