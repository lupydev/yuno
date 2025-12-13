"""
Authentication router

Handles user login and token refresh endpoints.
"""

from fastapi import APIRouter, status

from app.core.db import SessionDep
from app.domain.schemas import LoginRequest, LoginResponse, UserData
from app.services.auth import AuthService

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
    # Authenticate user
    user = AuthService.authenticate_user(
        db, credentials.email, credentials.password)

    # Generate tokens
    tokens = AuthService.generate_tokens(str(user.id))

    # Prepare user data response
    user_data = UserData(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
    )

    return LoginResponse(
        token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
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
