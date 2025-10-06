import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.inspector_service import InspectorService
from app.models import Inspector, User, UserRole, generate_uuid
from app.schemas.auth import UserRegister
from app.services.auth_service import AuthService


class TestInspectorServiceCreate:
    """Test the create service method."""

    @pytest.fixture
    def inspector_user(self, db_session: Session) -> User:
        """Create a user with INSPECTOR role."""
        auth_service = AuthService(db_session)
        return auth_service.register_user(UserRegister(
            name="Inspector User",
            email="inspector@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))

    def test_create_inspector_profile(self, db_session: Session, inspector_user: User):
        """Can create inspector profile for inspector user."""
        service = InspectorService(db_session)
        result = service.create(inspector_user.id, "EMP001")

        assert result.user_id == inspector_user.id
        assert result.employee_id == "EMP001"
        assert result.active is True

    def test_create_uppercases_employee_id(self, db_session: Session, inspector_user: User):
        """Create uppercases the employee ID."""
        service = InspectorService(db_session)
        result = service.create(inspector_user.id, "emp001")

        assert result.employee_id == "EMP001"

    def test_cannot_create_for_nonexistent_user(self, db_session: Session):
        """Cannot create inspector for nonexistent user."""
        service = InspectorService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.create(generate_uuid(), "EMP001")

        assert exc_info.value.status_code == 404

    def test_cannot_create_for_non_inspector_role(self, db_session: Session):
        """Cannot create inspector profile for non-inspector user."""
        auth_service = AuthService(db_session)
        client_user = auth_service.register_user(UserRegister(
            name="Client User",
            email="client@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        service = InspectorService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.create(client_user.id, "EMP001")

        assert exc_info.value.status_code == 400
        assert "INSPECTOR" in exc_info.value.detail

    def test_cannot_create_duplicate_for_user(self, db_session: Session, inspector_user: User):
        """Cannot create multiple inspector profiles for same user."""
        service = InspectorService(db_session)
        service.create(inspector_user.id, "EMP001")

        with pytest.raises(HTTPException) as exc_info:
            service.create(inspector_user.id, "EMP002")

        assert exc_info.value.status_code == 400
        assert "ya tiene" in exc_info.value.detail.lower()

    def test_cannot_create_duplicate_employee_id(self, db_session: Session):
        """Cannot create inspectors with duplicate employee IDs."""
        auth_service = AuthService(db_session)
        user1 = auth_service.register_user(UserRegister(
            name="Inspector 1",
            email="inspector1@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))
        user2 = auth_service.register_user(UserRegister(
            name="Inspector 2",
            email="inspector2@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))

        service = InspectorService(db_session)
        service.create(user1.id, "EMP001")

        with pytest.raises(HTTPException) as exc_info:
            service.create(user2.id, "EMP001")

        assert exc_info.value.status_code == 400
        assert "empleado" in exc_info.value.detail.lower()


class TestInspectorServiceList:
    """Test the list service method."""

    def test_list_returns_all_inspectors(self, db_session: Session):
        """List returns all inspectors."""
        auth_service = AuthService(db_session)
        user1 = auth_service.register_user(UserRegister(
            name="Inspector 1",
            email="inspector1@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))
        user2 = auth_service.register_user(UserRegister(
            name="Inspector 2",
            email="inspector2@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))

        inspector_service = InspectorService(db_session)
        inspector_service.create(user1.id, "EMP001")
        inspector_service.create(user2.id, "EMP002")

        inspectors, total = inspector_service.list(page=1, page_size=10)

        assert total == 2
        assert len(inspectors) == 2

    def test_list_pagination_works(self, db_session: Session):
        """List pagination works correctly."""
        auth_service = AuthService(db_session)
        inspector_service = InspectorService(db_session)

        # Create 3 inspectors
        for i in range(3):
            user = auth_service.register_user(UserRegister(
                name=f"Inspector {i}",
                email=f"inspector{i}@test.com",
                password="Password123",
                role=UserRole.INSPECTOR
            ))
            inspector_service.create(user.id, f"EMP00{i}")

        inspectors, total = inspector_service.list(page=1, page_size=2)

        assert total == 3
        assert len(inspectors) == 2

    def test_list_filter_by_active(self, db_session: Session):
        """List can filter by active status."""
        auth_service = AuthService(db_session)
        user1 = auth_service.register_user(UserRegister(
            name="Inspector 1",
            email="inspector1@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))
        user2 = auth_service.register_user(UserRegister(
            name="Inspector 2",
            email="inspector2@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))

        inspector_service = InspectorService(db_session)
        inspector1 = inspector_service.create(user1.id, "EMP001")
        inspector2 = inspector_service.create(user2.id, "EMP002")

        # Deactivate first inspector
        inspector_service.update(inspector1.id, active=False)

        active_inspectors, total = inspector_service.list(page=1, page_size=10, active_only=True)

        assert total == 1
        assert active_inspectors[0].id == inspector2.id


class TestInspectorServiceGet:
    """Test the get service method."""

    def test_get_returns_inspector(self, db_session: Session):
        """Get returns the inspector by ID."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Inspector",
            email="inspector@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))

        inspector_service = InspectorService(db_session)
        inspector = inspector_service.create(user.id, "EMP001")

        result = inspector_service.get(inspector.id)

        assert result.id == inspector.id
        assert result.employee_id == "EMP001"

    def test_get_nonexistent_raises_404(self, db_session: Session):
        """Get with nonexistent ID raises 404."""
        service = InspectorService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.get(generate_uuid())

        assert exc_info.value.status_code == 404


class TestInspectorServiceUpdate:
    """Test the update service method."""

    def test_update_employee_id(self, db_session: Session):
        """Can update employee ID."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Inspector",
            email="inspector@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))

        inspector_service = InspectorService(db_session)
        inspector = inspector_service.create(user.id, "EMP001")

        result = inspector_service.update(inspector.id, employee_id="EMP999")

        assert result.employee_id == "EMP999"

    def test_update_active_status(self, db_session: Session):
        """Can update active status."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Inspector",
            email="inspector@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))

        inspector_service = InspectorService(db_session)
        inspector = inspector_service.create(user.id, "EMP001")

        result = inspector_service.update(inspector.id, active=False)

        assert result.active is False

    def test_update_nonexistent_raises_404(self, db_session: Session):
        """Update nonexistent inspector raises 404."""
        service = InspectorService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.update(generate_uuid(), employee_id="NEW")

        assert exc_info.value.status_code == 404

    def test_cannot_update_to_duplicate_employee_id(self, db_session: Session):
        """Cannot update to duplicate employee ID."""
        auth_service = AuthService(db_session)
        user1 = auth_service.register_user(UserRegister(
            name="Inspector 1",
            email="inspector1@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))
        user2 = auth_service.register_user(UserRegister(
            name="Inspector 2",
            email="inspector2@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))

        inspector_service = InspectorService(db_session)
        inspector1 = inspector_service.create(user1.id, "EMP001")
        inspector2 = inspector_service.create(user2.id, "EMP002")

        with pytest.raises(HTTPException) as exc_info:
            inspector_service.update(inspector2.id, employee_id="EMP001")

        assert exc_info.value.status_code == 400


class TestInspectorServiceDelete:
    """Test the delete service method."""

    def test_delete_inspector(self, db_session: Session):
        """Can delete inspector profile."""
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Inspector",
            email="inspector@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))

        inspector_service = InspectorService(db_session)
        inspector = inspector_service.create(user.id, "EMP001")

        inspector_service.delete(inspector.id)

        # Verify it was deleted
        assert db_session.query(Inspector).filter(Inspector.id == inspector.id).first() is None

    def test_delete_nonexistent_raises_404(self, db_session: Session):
        """Delete nonexistent inspector raises 404."""
        service = InspectorService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.delete(generate_uuid())

        assert exc_info.value.status_code == 404
