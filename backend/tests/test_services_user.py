import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.models import User, UserRole, UserSession, generate_uuid
from app.schemas.auth import UserRegister
from datetime import datetime, timezone


class TestUserServiceGetCurrentUser:
    """Test the get_current_user service method."""

    def test_returns_same_user(self, db_session: Session):
        """get_current_user returns the same user object."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Test User",
            email="test@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        service = UserService(db_session)
        result = service.get_current_user(user)

        assert result.id == user.id


class TestUserServiceUpdateCurrentUser:
    """Test the update_current_user service method."""

    def test_can_update_name(self, db_session: Session):
        """User can update their own name."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Old Name",
            email="test@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        service = UserService(db_session)
        result = service.update_current_user(user, name="New Name")

        assert result.name == "New Name"

    def test_can_update_email(self, db_session: Session):
        """User can update their own email."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Test User",
            email="old@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        service = UserService(db_session)
        result = service.update_current_user(user, email="new@test.com")

        assert result.email == "new@test.com"

    def test_cannot_update_role(self, db_session: Session):
        """User cannot update their own role - role parameter doesn't exist."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Test User",
            email="test@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        service = UserService(db_session)

        # Method doesn't accept role parameter, so it raises TypeError
        with pytest.raises(TypeError):
            service.update_current_user(user, role=UserRole.ADMIN)

    def test_cannot_update_active_status(self, db_session: Session):
        """User cannot update their own active status."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Test User",
            email="test@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        service = UserService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.update_current_user(user, is_active=False)

        assert exc_info.value.status_code == 403

    def test_cannot_update_to_existing_email(self, db_session: Session):
        """User cannot update email to one that already exists."""
        auth_service = AuthService(db_session)
        user1 = auth_service.register_user(UserRegister(
            name="User 1",
            email="user1@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))
        user2 = auth_service.register_user(UserRegister(
            name="User 2",
            email="user2@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        service = UserService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.update_current_user(user2, email="user1@test.com")

        assert exc_info.value.status_code == 400


class TestUserServiceChangePassword:
    """Test the change_password service method."""

    def test_can_change_password(self, db_session: Session):
        """User can change their password with correct current password."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Test User",
            email="test@test.com",
            password="OldPassword123",
            role=UserRole.CLIENT
        ))

        service = UserService(db_session)
        service.change_password(user, "OldPassword123", "NewPassword456")

        # Verify new password works
        from app.core.security import verify_password
        db_session.refresh(user)
        assert verify_password("NewPassword456", user.password_hash)

    def test_change_password_revokes_sessions(self, db_session: Session):
        """Changing password revokes all active sessions."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Test User",
            email="test@test.com",
            password="OldPassword123",
            role=UserRole.CLIENT
        ))

        # Create a session
        token, _ = auth_service.login("test@test.com", "OldPassword123")

        service = UserService(db_session)
        service.change_password(user, "OldPassword123", "NewPassword456")

        # Verify session was revoked
        session = db_session.query(UserSession).filter(
            UserSession.token == token
        ).first()
        assert session.revoked_at is not None

    def test_cannot_change_with_wrong_current_password(self, db_session: Session):
        """Cannot change password with incorrect current password."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Test User",
            email="test@test.com",
            password="OldPassword123",
            role=UserRole.CLIENT
        ))

        service = UserService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.change_password(user, "WrongPassword", "NewPassword456")

        assert exc_info.value.status_code == 400


class TestUserServiceCreate:
    """Test the create service method (admin operation)."""

    def test_can_create_user(self, db_session: Session):
        """Admin can create a new user."""
        service = UserService(db_session)
        user = service.create(
            name="New User",
            email="newuser@test.com",
            password="Password123",
            role=UserRole.CLIENT,
            is_active=True
        )

        assert user.id is not None
        assert user.name == "New User"
        assert user.email == "newuser@test.com"
        assert user.role == UserRole.CLIENT
        assert user.is_active is True

        # Verify password was hashed
        from app.core.security import verify_password
        assert verify_password("Password123", user.password_hash)

    def test_cannot_create_duplicate_email(self, db_session: Session):
        """Cannot create user with existing email."""
        service = UserService(db_session)

        # Create first user
        service.create(
            name="First User",
            email="duplicate@test.com",
            password="Password123",
            role=UserRole.CLIENT
        )

        # Try to create second user with same email
        with pytest.raises(HTTPException) as exc_info:
            service.create(
                name="Second User",
                email="duplicate@test.com",
                password="Password456",
                role=UserRole.CLIENT
            )

        assert exc_info.value.status_code == 400

    def test_can_create_with_different_roles(self, db_session: Session):
        """Can create users with different roles."""
        service = UserService(db_session)

        admin = service.create(
            name="Admin User",
            email="admin@test.com",
            password="Password123",
            role=UserRole.ADMIN
        )

        inspector = service.create(
            name="Inspector User",
            email="inspector@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        )

        client = service.create(
            name="Client User",
            email="client@test.com",
            password="Password123",
            role=UserRole.CLIENT
        )

        assert admin.role == UserRole.ADMIN
        assert inspector.role == UserRole.INSPECTOR
        assert client.role == UserRole.CLIENT


class TestUserServiceList:
    """Test the list service method."""

    def test_list_returns_all_users(self, db_session: Session):
        """List returns all users."""
        auth_service = AuthService(db_session)
        auth_service.register_user(UserRegister(
            name="User 1",
            email="user1@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))
        auth_service.register_user(UserRegister(
            name="User 2",
            email="user2@test.com",
            password="Password123",
            role=UserRole.ADMIN
        ))

        service = UserService(db_session)
        users, total = service.list(page=1, page_size=10)

        assert total == 2
        assert len(users) == 2

    def test_list_filter_by_role(self, db_session: Session):
        """List can filter by role."""
        auth_service = AuthService(db_session)
        auth_service.register_user(UserRegister(
            name="Client",
            email="client@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))
        auth_service.register_user(UserRegister(
            name="Admin",
            email="admin@test.com",
            password="Password123",
            role=UserRole.ADMIN
        ))

        service = UserService(db_session)
        users, total = service.list(page=1, page_size=10, role=UserRole.CLIENT)

        assert total == 1
        assert users[0].role == UserRole.CLIENT

    def test_list_filter_by_active_status(self, db_session: Session):
        """List can filter by active status."""
        auth_service = AuthService(db_session)
        user1 = auth_service.register_user(UserRegister(
            name="Active User",
            email="active@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))
        user2 = auth_service.register_user(UserRegister(
            name="Inactive User",
            email="inactive@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        # Deactivate second user
        user2.is_active = False
        db_session.commit()

        service = UserService(db_session)
        users, total = service.list(page=1, page_size=10, active_only=True)

        assert total == 1
        assert users[0].id == user1.id

    def test_list_search_by_name(self, db_session: Session):
        """List can search by name."""
        auth_service = AuthService(db_session)
        auth_service.register_user(UserRegister(
            name="John Doe",
            email="john@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))
        auth_service.register_user(UserRegister(
            name="Jane Smith",
            email="jane@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        service = UserService(db_session)
        users, total = service.list(page=1, page_size=10, search="John")

        assert total == 1
        assert users[0].name == "John Doe"


class TestUserServiceGet:
    """Test the get service method."""

    def test_get_returns_user(self, db_session: Session):
        """Get returns the user by ID."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Test User",
            email="test@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        service = UserService(db_session)
        result = service.get(user.id)

        assert result.id == user.id

    def test_get_nonexistent_raises_404(self, db_session: Session):
        """Get with nonexistent ID raises 404."""
        service = UserService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.get(generate_uuid())

        assert exc_info.value.status_code == 404


class TestUserServiceUpdate:
    """Test the update service method (admin operation)."""

    def test_admin_can_deactivate_user(self, db_session: Session):
        """Admin can deactivate user."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Test User",
            email="test@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        # Create a session
        token, _ = auth_service.login("test@test.com", "Password123")

        service = UserService(db_session)
        result = service.update(user.id, is_active=False)

        assert result.is_active is False

        # Verify session was revoked
        session = db_session.query(UserSession).filter(
            UserSession.token == token
        ).first()
        assert session.revoked_at is not None


class TestUserServiceDelete:
    """Test the delete service method."""

    def test_can_delete_user(self, db_session: Session):
        """Can delete user."""
        auth_service = AuthService(db_session)
        admin = auth_service.register_user(UserRegister(
            name="Admin",
            email="admin@test.com",
            password="Password123",
            role=UserRole.ADMIN
        ))
        user = auth_service.register_user(UserRegister(
            name="Test User",
            email="test@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        service = UserService(db_session)
        service.delete(user.id, admin.id)

        # Verify it was deleted
        assert db_session.query(User).filter(User.id == user.id).first() is None

    def test_cannot_delete_self(self, db_session: Session):
        """Cannot delete own account."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Test User",
            email="test@test.com",
            password="Password123",
            role=UserRole.ADMIN
        ))

        service = UserService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.delete(user.id, user.id)

        assert exc_info.value.status_code == 400
