from tests.conftest import utc_now
import pytest
from datetime import datetime
from app.models import User, UserRole, UserSession, Inspector


class TestUserModel:
    def test_create_user(self, db_session):
        """Test creating a basic user."""
        user = User(
            id="user-1",
            name="John Doe",
            email="john@example.com",
            role=UserRole.CLIENT,
            password_hash="hashed_pw",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        retrieved = db_session.query(User).filter_by(id="user-1").first()
        assert retrieved is not None
        assert retrieved.name == "John Doe"
        assert retrieved.email == "john@example.com"
        assert retrieved.role == UserRole.CLIENT
        assert retrieved.is_active is True

    def test_user_unique_email(self, db_session):
        """Test that email must be unique."""
        user1 = User(
            id="user-1",
            name="User One",
            email="duplicate@example.com",
            role=UserRole.CLIENT,
            password_hash="hash1",
        )
        user2 = User(
            id="user-2",
            name="User Two",
            email="duplicate@example.com",
            role=UserRole.CLIENT,
            password_hash="hash2",
        )
        db_session.add(user1)
        db_session.commit()

        db_session.add(user2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_user_roles(self, db_session):
        """Test different user roles."""
        client = User(
            id="client-1",
            name="Client User",
            email="client@example.com",
            role=UserRole.CLIENT,
            password_hash="hash",
        )
        inspector = User(
            id="inspector-1",
            name="Inspector User",
            email="inspector@example.com",
            role=UserRole.INSPECTOR,
            password_hash="hash",
        )
        admin = User(
            id="admin-1",
            name="Admin User",
            email="admin@example.com",
            role=UserRole.ADMIN,
            password_hash="hash",
        )

        db_session.add_all([client, inspector, admin])
        db_session.commit()

        assert db_session.query(User).filter_by(role=UserRole.CLIENT).count() == 1
        assert db_session.query(User).filter_by(role=UserRole.INSPECTOR).count() == 1
        assert db_session.query(User).filter_by(role=UserRole.ADMIN).count() == 1

    def test_user_last_login_tracking(self, db_session):
        """Test that last_login_at can be updated."""
        user = User(
            id="user-1",
            name="Test User",
            email="test@example.com",
            role=UserRole.CLIENT,
            password_hash="hash",
        )
        db_session.add(user)
        db_session.commit()

        assert user.last_login_at is None

        login_time = utc_now()
        user.last_login_at = login_time
        db_session.commit()

        retrieved = db_session.query(User).filter_by(id="user-1").first()
        assert retrieved.last_login_at is not None

    def test_user_repr(self, sample_user):
        """Test user string representation."""
        repr_str = repr(sample_user)
        assert "User" in repr_str
        assert sample_user.id in repr_str
        assert sample_user.email in repr_str


class TestUserSessionModel:
    def test_create_session(self, db_session, sample_user):
        """Test creating a user session."""
        session = UserSession(
            id="session-1",
            user_id=sample_user.id,
            token="test-token-123",
            expires_at=utc_now(),
        )
        db_session.add(session)
        db_session.commit()

        retrieved = db_session.query(UserSession).filter_by(id="session-1").first()
        assert retrieved is not None
        assert retrieved.user_id == sample_user.id
        assert retrieved.token == "test-token-123"

    def test_session_unique_token(self, db_session, sample_user):
        """Test that session tokens must be unique."""
        session1 = UserSession(
            id="session-1",
            user_id=sample_user.id,
            token="duplicate-token",
            expires_at=utc_now(),
        )
        session2 = UserSession(
            id="session-2",
            user_id=sample_user.id,
            token="duplicate-token",
            expires_at=utc_now(),
        )

        db_session.add(session1)
        db_session.commit()

        db_session.add(session2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_session_revocation(self, db_session, sample_user):
        """Test revoking a session."""
        session = UserSession(
            id="session-1",
            user_id=sample_user.id,
            token="token-to-revoke",
            expires_at=utc_now(),
        )
        db_session.add(session)
        db_session.commit()

        assert session.revoked_at is None

        revoke_time = utc_now()
        session.revoked_at = revoke_time
        db_session.commit()

        retrieved = db_session.query(UserSession).filter_by(id="session-1").first()
        assert retrieved.revoked_at is not None

    def test_session_cascade_delete(self, db_session, sample_user):
        """Test that sessions are deleted when user is deleted."""
        session = UserSession(
            id="session-1",
            user_id=sample_user.id,
            token="token-123",
            expires_at=utc_now(),
        )
        db_session.add(session)
        db_session.commit()

        db_session.delete(sample_user)
        db_session.commit()

        assert db_session.query(UserSession).filter_by(id="session-1").first() is None


class TestInspectorModel:
    def test_create_inspector(self, db_session, sample_inspector_user):
        """Test creating an inspector profile."""
        inspector = Inspector(
            id="inspector-1",
            user_id=sample_inspector_user.id,
            employee_id="INS-001",
            active=True,
        )
        db_session.add(inspector)
        db_session.commit()

        retrieved = db_session.query(Inspector).filter_by(id="inspector-1").first()
        assert retrieved is not None
        assert retrieved.user_id == sample_inspector_user.id
        assert retrieved.employee_id == "INS-001"
        assert retrieved.active is True

    def test_inspector_unique_employee_id(self, db_session, sample_inspector_user):
        """Test that employee_id must be unique."""
        user2 = User(
            id="user-2",
            name="Second Inspector",
            email="inspector2@example.com",
            role=UserRole.INSPECTOR,
            password_hash="hash",
        )
        db_session.add(user2)
        db_session.commit()

        inspector1 = Inspector(
            id="inspector-1",
            user_id=sample_inspector_user.id,
            employee_id="INS-DUPLICATE",
            active=True,
        )
        inspector2 = Inspector(
            id="inspector-2",
            user_id=user2.id,
            employee_id="INS-DUPLICATE",
            active=True,
        )

        db_session.add(inspector1)
        db_session.commit()

        db_session.add(inspector2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_inspector_one_per_user(self, db_session, sample_inspector_user):
        """Test that each user can only have one inspector profile."""
        inspector1 = Inspector(
            id="inspector-1",
            user_id=sample_inspector_user.id,
            employee_id="INS-001",
            active=True,
        )
        inspector2 = Inspector(
            id="inspector-2",
            user_id=sample_inspector_user.id,
            employee_id="INS-002",
            active=True,
        )

        db_session.add(inspector1)
        db_session.commit()

        db_session.add(inspector2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_inspector_deactivation(self, db_session, sample_inspector):
        """Test deactivating an inspector."""
        assert sample_inspector.active is True

        sample_inspector.active = False
        db_session.commit()

        retrieved = db_session.query(Inspector).filter_by(id=sample_inspector.id).first()
        assert retrieved.active is False

    def test_inspector_repr(self, sample_inspector):
        """Test inspector string representation."""
        repr_str = repr(sample_inspector)
        assert "Inspector" in repr_str
        assert sample_inspector.employee_id in repr_str
