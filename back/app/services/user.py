from uuid import UUID

from app.core.db import SessionDep
from app.core.security import hash_password
from app.models.user import Roles, User
from app.schemas.user import AdminUserUpdate, UserCreateInternal
from fastapi import HTTPException, status
from pydantic import EmailStr
from sqlmodel import func, or_, select


class UserService:
    @staticmethod
    def create_user(
        db: SessionDep,
        current_user: UUID,
        data: UserCreateInternal,
    ) -> User:
        """Create a new user under the tenant owner

        Args:
            db (SessionDep): database session
            current_user (UUID): tenant owner ID to assign to the new user
            data (UserCreateInternal): data for creating the new user

        Raises:
            HTTPException: if the email already exists

        Returns:
            User: the newly created user
        """
        # Validate unique email
        existing = db.exec(select(User).where(User.email == data.email)).one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists"
            )

        user = User(
            **data.model_dump(exclude={"password"}),
            hashed_password=hash_password(data.password),
            owner_id=current_user,
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_users(
        db: SessionDep,
        current_user: UUID,
        skip: int,
        limit: int,
        role: Roles | None = None,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        """Retrieve a paginated list of users for the tenant owner

        Args:
            db (SessionDep): database session
            current_user (UUID): tenant owner ID for filtering
            skip (int): number of items to skip
            limit (int): number of items to retrieve
            role (Roles | None): filter by role
            search (str | None): search by name (first_name or last_name)

        Returns:
            tuple[list[User], int]: list of users and total count
        """

        # Base filter for tenant
        base_filter = or_(
            User.owner_id == current_user,  # usuarios del tenant
            User.id == current_user,  # incluir al owner
        )

        # Build filters list
        filters = [base_filter]

        if role:
            filters.append(User.role == role.value)  # type: ignore

        if search:
            search_filter = or_(
                User.name.ilike(f"%{search}%"),  # type: ignore
                User.surname.ilike(f"%{search}%"),  # type: ignore
            )
            filters.append(search_filter)

        total_items = db.exec(select(func.count()).select_from(User).where(*filters)).one()

        users = db.exec(select(User).where(*filters).offset(skip).limit(limit)).all()

        return list(users), total_items

    @staticmethod
    def get_user_by_id(db: SessionDep, id: UUID, current_user: UUID) -> User:
        """Retrieve a user by ID for the tenant owner

        Args:
            db (SessionDep): database session
            id (UUID): user ID
            current_user (UUID): tenant owner ID for validation

        Raises:
            HTTPException: if the user is not found or does not belong to the tenant

        Returns:
            User: the retrieved user
        """
        user = db.get(User, id)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return user

    @staticmethod
    def soft_delete_user(db: SessionDep, id: UUID, current_user: UUID):
        """Soft delete a user by setting is_active to False

        Args:
            db (SessionDep): database session
            id (UUID): user ID
            current_user (UUID): tenant owner ID for validation

        Raises:
            HTTPException: if the user is not found or does not belong to the tenant
        """
        user = db.get(User, id)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.is_active = False
        db.add(user)
        db.commit()

    @staticmethod
    def update_user(
        db: SessionDep,
        user_id: UUID,
        data: AdminUserUpdate,
        current_user: UUID,
        user: User | None = None,
    ) -> User:
        """Update user information (name, surname, email, and role if allowed)

        Args:
            db (SessionDep): database session
            user_id (UUID): ID of user to update
            data: AdminUserUpdate data for updating the user
            current_user (UUID): tenant owner ID for validation
            user (User | None): pre-fetched user to avoid duplicate query (optional)

        Raises:
            HTTPException: if user not found or permission denied

        Returns:
            User: updated user
        """
        # Si no se proporcionó el usuario, buscarlo
        if user is None:
            user = db.get(User, user_id)

            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            # Determinar el ID del owner del tenant
            user_current_user = UserService._get_current_user(user)

            # Validar que pertenezca al mismo tenant
            if user_current_user != current_user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        update_data = data.model_dump(exclude_unset=True)

        # Aplicar actualizaciones
        for key, value in update_data.items():
            setattr(user, key, value)

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def get_user_by_email(db: SessionDep, email: EmailStr, current_user: UUID) -> User:
        """Retrieve a user by email for the tenant owner

        Args:
            db (SessionDep): database session
            email (EmailStr): user email
            current_user (UUID): tenant owner ID for filtering

        Raises:
            HTTPException: if the user is not found or does not belong to the tenant

        Returns:
            User: the retrieved user
        """
        user = db.exec(
            select(User).where(
                User.email == email,
                or_(
                    User.owner_id == current_user,
                    User.id == current_user,
                ),
            )
        ).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return user
