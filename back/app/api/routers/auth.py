"""
Authentication router

Handles user login and token refresh endpoints.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.domain.schemas import LoginRequest, LoginResponse, TokenPayload, UserData
from app.core.db import SessionDep
from app.core.security import create_access_token, create_refresh_token, verify_password
from app.models import User

router = APIRouter()


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(credentials: LoginRequest, db: SessionDep) -> LoginResponse:
    """
    Authenticate user and generate access tokens

    **Flow:**
    1. Validate email exists
    2. Verify password hash
    3. Check if account is active
    4. Generate access and refresh tokens
    5. Return user data with tokens

    **Errors:**
    - 401: Invalid credentials or inactive account

    **Example:**
    ```json
    {
      "email": "admin@yknow.com",
      "password": "securepassword"
    }
    ```
    """
    # Find user by email
    statement = select(User).where(User.email == credentials.email)
    user = db.exec(statement).first()

    # Validate credentials
    if not user or not verify_password(credentials.password, user.password):
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

    # Generate tokens
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    # Prepare user data response
    user_data = UserData(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
    )

    return LoginResponse(
        token=access_token,
        refresh_token=refresh_token,
        user_data=user_data,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout() -> dict[str, str]:
    """
    Logout endpoint

    Client should discard tokens after calling this endpoint.
    For a more robust implementation, consider implementing token blacklisting.

    **Returns:**
    Success message
    """
    return {"message": "Logged out successfully"}
