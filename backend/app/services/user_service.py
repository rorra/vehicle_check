from typing import List, Optional, Tuple
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.security import verify_password, get_password_hash
from app.models import User, UserSession, UserRole, generate_uuid


class UserService:
    """Service layer for user business logic."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
        email: str,
        password: str,
        role: UserRole = UserRole.CLIENT,
        is_active: bool = True
    ) -> User:
        """
        Create a new user (admin operation).

        Args:
            name: User's full name
            email: User's email address
            password: User's password (will be hashed)
            role: User's role (default: CLIENT)
            is_active: Whether user is active (default: True)

        Returns:
            The created user

        Raises:
            HTTPException: If email already exists
        """
        # Check if email already exists
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un usuario con este correo electrónico"
            )

        # Create new user
        hashed_password = get_password_hash(password)
        new_user = User(
            id=generate_uuid(),
            name=name,
            email=email,
            password_hash=hashed_password,
            role=role,
            is_active=is_active,
        )

        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        return new_user

    def get_current_user(self, user: User) -> User:
        """
        Get current user's profile.

        Args:
            user: The current user

        Returns:
            The user object
        """
        return user

    def update_current_user(
        self,
        user: User,
        name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> User:
        """
        Update current user's profile.

        Args:
            user: The current user
            name: New name (optional)
            email: New email (optional)
            role: New role (optional, not allowed for self-update)
            is_active: New active status (optional, not allowed for self-update)

        Returns:
            The updated user

        Raises:
            HTTPException: If trying to change role/active status or email conflict
        """
        # Users cannot change their own role or active status
        if role is not None or is_active is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes cambiar tu propio rol o estado activo"
            )

        # Check if new email already exists
        if email and email != user.email:
            existing = self.db.query(User).filter(User.email == email).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un usuario con este correo electrónico"
                )

        # Update fields
        if name is not None:
            user.name = name
        if email is not None:
            user.email = email

        self.db.commit()
        self.db.refresh(user)

        return user

    def change_password(self, user: User, current_password: str, new_password: str) -> None:
        """
        Change current user's password.

        Args:
            user: The current user
            current_password: Current password for verification
            new_password: New password

        Raises:
            HTTPException: If current password is incorrect
        """
        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contraseña actual incorrecta"
            )

        # Update password
        user.password_hash = get_password_hash(new_password)

        # Revoke all existing sessions
        self.db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None)
        ).update({"revoked_at": datetime.now(timezone.utc)})

        self.db.commit()

    def list(
        self,
        page: int,
        page_size: int,
        role: Optional[UserRole] = None,
        active_only: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        """
        List all users with pagination and filters.

        Args:
            page: Page number
            page_size: Results per page
            role: Filter by role (optional)
            active_only: Filter by active status (optional)
            search: Search by name or email (optional)

        Returns:
            Tuple of (users list, total count)
        """
        # Build query
        query = self.db.query(User)

        # Apply filters
        if role:
            query = query.filter(User.role == role)
        if active_only is not None:
            query = query.filter(User.is_active == active_only)
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(User.name.ilike(search_pattern), User.email.ilike(search_pattern))
            )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()

        return users, total

    def get(self, user_id: str) -> User:
        """
        Get user details by ID.

        Args:
            user_id: The user ID

        Returns:
            The user

        Raises:
            HTTPException: If user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        return user

    def update(
        self,
        user_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> User:
        """
        Update user details (admin operation).

        Args:
            user_id: The user ID
            name: New name (optional)
            email: New email (optional)
            role: New role (optional)
            is_active: New active status (optional)

        Returns:
            The updated user

        Raises:
            HTTPException: If user not found or email conflict
        """
        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Check if new email already exists
        if email and email != user.email:
            existing = self.db.query(User).filter(User.email == email).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un usuario con este correo electrónico"
                )

        # Update fields
        if name is not None:
            user.name = name
        if email is not None:
            user.email = email
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
            # If deactivating, revoke all sessions
            if not is_active:
                self.db.query(UserSession).filter(
                    UserSession.user_id == user.id,
                    UserSession.revoked_at.is_(None)
                ).update({"revoked_at": datetime.now(timezone.utc)})

        self.db.commit()
        self.db.refresh(user)

        return user

    def delete(self, user_id: str, current_user_id: str) -> None:
        """
        Delete a user.

        Args:
            user_id: The user ID to delete
            current_user_id: The current user's ID

        Raises:
            HTTPException: If user not found or trying to delete self
        """
        # Prevent self-deletion
        if user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes eliminar tu propia cuenta"
            )

        user = self.db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        self.db.delete(user)
        self.db.commit()
