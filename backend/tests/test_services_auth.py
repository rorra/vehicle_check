import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.auth_service import AuthService
from app.models import (
    User,
    UserRole,
    UserSession,
    generate_uuid,
)
from app.schemas.auth import UserRegister
from app.core.security import verify_password, create_access_token


class TestAuthServiceRegisterUser:
    """Test the register_user service method."""

    def test_successful_registration(self, db_session: Session):
        """Successfully register a new user."""
        service = AuthService(db_session)
        data = UserRegister(
            name="Test User",
            email="test@example.com",
            password="SecurePass123",
            role=UserRole.CLIENT
        )

        result = service.register_user(data)

        assert result.name == "Test User"
        assert result.email == "test@example.com"
        assert result.role == UserRole.CLIENT
        assert result.is_active is True
        assert verify_password("SecurePass123", result.password_hash)

    def test_cannot_register_duplicate_email(self, db_session: Session):
        """Cannot register with an email that already exists."""
        # Create first user
        service = AuthService(db_session)
        data1 = UserRegister(
            name="User One",
            email="duplicate@example.com",
            password="Password123",
            role=UserRole.CLIENT
        )
        service.register_user(data1)

        # Try to register with same email
        data2 = UserRegister(
            name="User Two",
            email="duplicate@example.com",
            password="DifferentPass456",
            role=UserRole.CLIENT
        )

        with pytest.raises(HTTPException) as exc_info:
            service.register_user(data2)

        assert exc_info.value.status_code == 400
        assert "ya está registrado" in exc_info.value.detail.lower()

    def test_password_is_hashed(self, db_session: Session):
        """Password is properly hashed, not stored in plain text."""
        service = AuthService(db_session)
        data = UserRegister(
            name="Test User",
            email="test@example.com",
            password="MySecretPassword",
            role=UserRole.CLIENT
        )

        result = service.register_user(data)

        # Password should not be stored in plain text
        assert result.password_hash != "MySecretPassword"
        # But should verify correctly
        assert verify_password("MySecretPassword", result.password_hash)

    def test_can_register_different_roles(self, db_session: Session):
        """Can register users with different roles."""
        service = AuthService(db_session)

        # Register as CLIENT
        client_data = UserRegister(
            name="Client User",
            email="client@example.com",
            password="Pass123",
            role=UserRole.CLIENT
        )
        client = service.register_user(client_data)
        assert client.role == UserRole.CLIENT

        # Register as ADMIN
        admin_data = UserRegister(
            name="Admin User",
            email="admin@example.com",
            password="Pass123",
            role=UserRole.ADMIN
        )
        admin = service.register_user(admin_data)
        assert admin.role == UserRole.ADMIN

        # Register as INSPECTOR
        inspector_data = UserRegister(
            name="Inspector User",
            email="inspector@example.com",
            password="Pass123",
            role=UserRole.INSPECTOR
        )
        inspector = service.register_user(inspector_data)
        assert inspector.role == UserRole.INSPECTOR


class TestAuthServiceLogin:
    """Test the login service method."""

    @pytest.fixture
    def registered_user(self, db_session: Session) -> User:
        """Create a registered user for login tests."""
        service = AuthService(db_session)
        data = UserRegister(
            name="Login Test User",
            email="login@example.com",
            password="CorrectPassword123",
            role=UserRole.CLIENT
        )
        return service.register_user(data)

    def test_successful_login(self, db_session: Session, registered_user: User):
        """Successfully login with correct credentials."""
        service = AuthService(db_session)

        access_token, user = service.login("login@example.com", "CorrectPassword123")

        assert access_token is not None
        assert user.id == registered_user.id
        assert user.email == registered_user.email

        # Verify session was created
        session = db_session.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.token == access_token
        ).first()
        assert session is not None
        assert session.revoked_at is None

    def test_login_updates_last_login(self, db_session: Session, registered_user: User):
        """Login updates the last_login_at timestamp."""
        service = AuthService(db_session)
        before_login = datetime.now(timezone.utc)

        access_token, user = service.login("login@example.com", "CorrectPassword123")

        # Refresh user from database
        db_session.refresh(user)
        assert user.last_login_at is not None
        # Database stores as naive datetime and truncates microseconds
        last_login_naive = user.last_login_at.replace(tzinfo=timezone.utc) if user.last_login_at.tzinfo is None else user.last_login_at
        # Allow 1 second tolerance for database precision
        time_diff = abs((last_login_naive - before_login).total_seconds())
        assert time_diff < 1

    def test_login_with_wrong_password(self, db_session: Session, registered_user: User):
        """Cannot login with incorrect password."""
        service = AuthService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.login("login@example.com", "WrongPassword")

        assert exc_info.value.status_code == 401
        assert "incorrectos" in exc_info.value.detail.lower()

    def test_login_with_nonexistent_email(self, db_session: Session):
        """Cannot login with email that doesn't exist."""
        service = AuthService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.login("nonexistent@example.com", "AnyPassword")

        assert exc_info.value.status_code == 401

    def test_login_with_inactive_user(self, db_session: Session, registered_user: User):
        """Cannot login if user is inactive."""
        # Deactivate user
        registered_user.is_active = False
        db_session.commit()

        service = AuthService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.login("login@example.com", "CorrectPassword123")

        assert exc_info.value.status_code == 400
        assert "inactivo" in exc_info.value.detail.lower()

    def test_multiple_sessions_can_exist(self, db_session: Session, registered_user: User):
        """Multiple active sessions can exist for one user."""
        service = AuthService(db_session)

        # Login twice
        token1, user1 = service.login("login@example.com", "CorrectPassword123")
        token2, user2 = service.login("login@example.com", "CorrectPassword123")

        assert token1 != token2

        # Both sessions should exist
        sessions = db_session.query(UserSession).filter(
            UserSession.user_id == registered_user.id,
            UserSession.revoked_at.is_(None)
        ).all()
        assert len(sessions) == 2


class TestAuthServiceRequestPasswordReset:
    """Test the request_password_reset service method."""

    @pytest.fixture
    def registered_user(self, db_session: Session) -> User:
        """Create a registered user."""
        service = AuthService(db_session)
        data = UserRegister(
            name="Reset Test User",
            email="reset@example.com",
            password="Password123",
            role=UserRole.CLIENT
        )
        return service.register_user(data)

    def test_request_reset_for_existing_user(
        self,
        db_session: Session,
        registered_user: User,
        monkeypatch
    ):
        """Request password reset for existing user sends email."""
        # Mock the email sending function
        email_sent = []

        def mock_send_email(email, token):
            email_sent.append((email, token))

        # Mock on the auth_service module where it's imported
        from app.services import auth_service
        monkeypatch.setattr(auth_service, "send_password_reset_email", mock_send_email)

        service = AuthService(db_session)
        result = service.request_password_reset("reset@example.com")

        assert result is True
        assert len(email_sent) == 1
        assert email_sent[0][0] == "reset@example.com"
        assert email_sent[0][1] is not None  # Token was generated

    def test_request_reset_for_nonexistent_user(self, db_session: Session):
        """Request password reset for non-existent user returns False."""
        service = AuthService(db_session)
        result = service.request_password_reset("nonexistent@example.com")

        assert result is False

    def test_request_reset_does_not_reveal_existence(
        self,
        db_session: Session,
        monkeypatch
    ):
        """Request doesn't reveal if email exists (returns same response)."""
        # This is tested at the route level, service returns bool
        # Just verify it doesn't crash for non-existent users
        service = AuthService(db_session)

        # Should not raise exception
        result = service.request_password_reset("any@email.com")
        assert result is False


class TestAuthServiceResetPassword:
    """Test the reset_password service method."""

    @pytest.fixture
    def registered_user(self, db_session: Session) -> User:
        """Create a registered user."""
        service = AuthService(db_session)
        data = UserRegister(
            name="Reset User",
            email="resetpass@example.com",
            password="OldPassword123",
            role=UserRole.CLIENT
        )
        return service.register_user(data)

    @pytest.fixture
    def reset_token(self, registered_user: User) -> str:
        """Generate a valid password reset token."""
        return create_access_token(
            data={"sub": registered_user.id, "type": "password_reset"},
            expires_delta=timedelta(hours=1)
        )

    def test_successful_password_reset(
        self,
        db_session: Session,
        registered_user: User,
        reset_token: str
    ):
        """Successfully reset password with valid token."""
        service = AuthService(db_session)

        service.reset_password(reset_token, "NewPassword456")

        # Verify password was changed
        db_session.refresh(registered_user)
        assert verify_password("NewPassword456", registered_user.password_hash)
        assert not verify_password("OldPassword123", registered_user.password_hash)

    def test_reset_revokes_all_sessions(
        self,
        db_session: Session,
        registered_user: User,
        reset_token: str
    ):
        """Password reset revokes all active sessions."""
        # Create some sessions
        service = AuthService(db_session)
        token1, _ = service.login("resetpass@example.com", "OldPassword123")
        token2, _ = service.login("resetpass@example.com", "OldPassword123")

        # Verify sessions exist
        active_sessions_before = db_session.query(UserSession).filter(
            UserSession.user_id == registered_user.id,
            UserSession.revoked_at.is_(None)
        ).count()
        assert active_sessions_before == 2

        # Reset password
        service.reset_password(reset_token, "NewPassword456")

        # Verify all sessions were revoked
        active_sessions_after = db_session.query(UserSession).filter(
            UserSession.user_id == registered_user.id,
            UserSession.revoked_at.is_(None)
        ).count()
        assert active_sessions_after == 0

    def test_reset_with_invalid_token(self, db_session: Session):
        """Cannot reset password with invalid token."""
        service = AuthService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.reset_password("invalid_token", "NewPassword")

        assert exc_info.value.status_code == 400
        assert "inválido" in exc_info.value.detail.lower()

    def test_reset_with_expired_token(self, db_session: Session, registered_user: User):
        """Cannot reset password with expired token."""
        # Create an expired token
        expired_token = create_access_token(
            data={"sub": registered_user.id, "type": "password_reset"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )

        service = AuthService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.reset_password(expired_token, "NewPassword")

        assert exc_info.value.status_code == 400

    def test_reset_with_wrong_token_type(self, db_session: Session, registered_user: User):
        """Cannot reset password with wrong token type."""
        # Create a regular access token (not password_reset type)
        wrong_type_token = create_access_token(
            data={"sub": registered_user.id, "type": "access"},
            expires_delta=timedelta(hours=1)
        )

        service = AuthService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.reset_password(wrong_type_token, "NewPassword")

        assert exc_info.value.status_code == 400
        assert "inválido" in exc_info.value.detail.lower()

    def test_reset_with_nonexistent_user(self, db_session: Session):
        """Cannot reset password for non-existent user."""
        # Create token with fake user ID
        fake_token = create_access_token(
            data={"sub": generate_uuid(), "type": "password_reset"},
            expires_delta=timedelta(hours=1)
        )

        service = AuthService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.reset_password(fake_token, "NewPassword")

        assert exc_info.value.status_code == 404


class TestAuthServiceLogout:
    """Test the logout service method."""

    @pytest.fixture
    def logged_in_user(self, db_session: Session):
        """Create a logged-in user with active session."""
        service = AuthService(db_session)

        # Register user
        data = UserRegister(
            name="Logout User",
            email="logout@example.com",
            password="Password123",
            role=UserRole.CLIENT
        )
        user = service.register_user(data)

        # Login to create session
        token, user = service.login("logout@example.com", "Password123")

        return user, token

    def test_successful_logout(self, db_session: Session, logged_in_user):
        """Successfully logout and revoke session."""
        user, token = logged_in_user
        service = AuthService(db_session)

        # Verify session is active
        session_before = db_session.query(UserSession).filter(
            UserSession.token == token,
            UserSession.revoked_at.is_(None)
        ).first()
        assert session_before is not None

        # Logout
        service.logout(token, user.id)

        # Verify session was revoked
        session_after = db_session.query(UserSession).filter(
            UserSession.token == token,
            UserSession.revoked_at.is_(None)
        ).first()
        assert session_after is None

        # Verify session still exists but is revoked
        revoked_session = db_session.query(UserSession).filter(
            UserSession.token == token
        ).first()
        assert revoked_session is not None
        assert revoked_session.revoked_at is not None

    def test_logout_with_nonexistent_session(self, db_session: Session, logged_in_user):
        """Logout with non-existent token doesn't raise error."""
        user, _ = logged_in_user
        service = AuthService(db_session)

        # Should not raise exception
        service.logout("nonexistent_token", user.id)

    def test_logout_only_revokes_specific_session(self, db_session: Session):
        """Logout only revokes the specific session, not all sessions."""
        service = AuthService(db_session)

        # Register and login twice
        data = UserRegister(
            name="Multi Session User",
            email="multi@example.com",
            password="Password123",
            role=UserRole.CLIENT
        )
        user = service.register_user(data)

        token1, _ = service.login("multi@example.com", "Password123")
        token2, _ = service.login("multi@example.com", "Password123")

        # Logout first session
        service.logout(token1, user.id)

        # Verify first session is revoked
        session1 = db_session.query(UserSession).filter(
            UserSession.token == token1
        ).first()
        assert session1.revoked_at is not None

        # Verify second session is still active
        session2 = db_session.query(UserSession).filter(
            UserSession.token == token2,
            UserSession.revoked_at.is_(None)
        ).first()
        assert session2 is not None

    def test_logout_already_revoked_session(self, db_session: Session, logged_in_user):
        """Logout already revoked session doesn't cause error."""
        user, token = logged_in_user
        service = AuthService(db_session)

        # Logout once
        service.logout(token, user.id)

        # Logout again - should not raise error
        service.logout(token, user.id)
