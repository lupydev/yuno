"""
User management router

API endpoints for user CRUD operations.
"""

from uuid import UUID

from fastapi import APIRouter, status

from app.domain.schemas.user import UserCreate, UserResponse, UserUpdate
from app.infraestructure.core.db import SessionDep
from app.models.user import Roles
from app.services.user import UserService

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate, db: SessionDep):
    """Create a new user"""
    return UserService.create_user(
        db,
        email=data.email,
        name=data.name,
        password=data.password,
        role=data.role,
        team_id=data.team_id,
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: SessionDep):
    """Get user by ID"""
    return UserService.get_user(db, user_id)


@router.get("/", response_model=list[UserResponse])
def list_users(db: SessionDep, skip: int = 0, limit: int = 100, role: Roles | None = None):
    """List all users with optional role filter"""
    return UserService.list_users(db, skip, limit, role)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: UUID, data: UserUpdate, db: SessionDep):
    """Update user information"""
    update_data = data.model_dump(exclude_unset=True)
    return UserService.update_user(db, user_id, **update_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: UUID, db: SessionDep):
    """Soft delete a user"""
    UserService.delete_user(db, user_id)
