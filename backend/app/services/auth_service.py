from datetime import timedelta, timezone, datetime
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.config import settings
from app.core.email import send_password_reset_email
from app.models import User, UserSession, UserRole, generate_uuid
from app.schemas.auth import UserRegister


class AuthService:
    """Service layer for authentication business logic."""

    def __init__(self, db: Session):
        self.db = db

    def register_user(self, user_data: UserRegister) -> User:
        """
        Register a new user.

        Args:
            user_data: The user registration data

        Returns:
            The created user

        Raises:
            HTTPException: If email already exists
        """
        # Check if email already exists
        existing_user = self._get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está registrado"
            )

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            id=generate_uuid(),
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
            role=user_data.role,
            is_active=True,
        )

        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        return new_user

    def login(self, email: str, password: str) -> Tuple[str, User]:
        """
        Authenticate user and create session.

        Args:
            email: User's email
            password: User's password

        Returns:
            Tuple of (access_token, user)

        Raises:
            HTTPException: If credentials are invalid or user is inactive
        """
        # Find user by email
        user = self._get_user_by_email(email)

        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo electrónico o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario inactivo"
            )

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)

        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email, "role": user.role.value, "jti": generate_uuid()},
            expires_delta=access_token_expires
        )

        # Create session record
        session = UserSession(
            id=generate_uuid(),
            user_id=user.id,
            token=access_token,
            expires_at=datetime.now(timezone.utc) + access_token_expires,
        )
        self.db.add(session)
        self.db.commit()

        return access_token, user

    def request_password_reset(self, email: str) -> bool:
        """
        Request password reset token.

        Args:
            email: User's email address

        Returns:
            True if reset email was sent, False otherwise
        """
        user = self._get_user_by_email(email)

        # Don't reveal if email exists or not for security
        if not user:
            return False

        # Create password reset token (valid for 1 hour)
        reset_token = create_access_token(
            data={"sub": user.id, "type": "password_reset"},
            expires_delta=timedelta(hours=1)
        )

        # Send password reset email
        send_password_reset_email(user.email, reset_token)

        return True

    def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset password using reset token.

        Args:
            token: Password reset token
            new_password: New password to set

        Raises:
            HTTPException: If token is invalid or user not found
        """
        # Decode and verify token
        payload = decode_access_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido o expirado"
            )

        user_id = payload.get("sub")
        token_type = payload.get("type")

        if not user_id or token_type != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token inválido"
            )

        # Find user
        user = self._get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Update password
        user.password_hash = get_password_hash(new_password)
        self.db.commit()

        # Revoke all existing sessions for security
        self._revoke_all_user_sessions(user.id)

    def logout(self, token: str, user_id: str) -> None:
        """
        Logout user by revoking the current session.

        Args:
            token: The JWT token to revoke
            user_id: The user's ID
        """
        # Revoke the current session
        session = self.db.query(UserSession).filter(
            UserSession.token == token,
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None)
        ).first()

        if session:
            session.revoked_at = datetime.now(timezone.utc)
            self.db.commit()

    # Private helper methods

    def _get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def _revoke_all_user_sessions(self, user_id: str) -> None:
        """Revoke all active sessions for a user."""
        self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None)
        ).update({"revoked_at": datetime.now(timezone.utc)})
        self.db.commit()
