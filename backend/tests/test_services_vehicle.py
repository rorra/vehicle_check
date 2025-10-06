import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.vehicle_service import VehicleService
from app.services.auth_service import AuthService
from app.models import User, UserRole, Vehicle, AnnualInspection, generate_uuid
from app.schemas.auth import UserRegister


class TestVehicleServiceCreate:
    """Test the create service method."""

    @pytest.fixture
    def client_user(self, db_session: Session) -> User:
        """Create a client user."""
        auth_service = AuthService(db_session)
        return auth_service.register_user(UserRegister(
            name="Client User",
            email="client@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

    @pytest.fixture
    def admin_user(self, db_session: Session) -> User:
        """Create an admin user."""
        auth_service = AuthService(db_session)
        return auth_service.register_user(UserRegister(
            name="Admin User",
            email="admin@test.com",
            password="Password123",
            role=UserRole.ADMIN
        ))

    def test_client_can_create_own_vehicle(self, db_session: Session, client_user: User):
        """Client can create vehicle for themselves."""
        service = VehicleService(db_session)
        result = service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        assert result.plate_number == "ABC123"
        assert result.owner_id == client_user.id

    def test_admin_can_create_for_specific_user(self, db_session: Session, admin_user: User, client_user: User):
        """Admin can create vehicle for specific user."""
        service = VehicleService(db_session)
        result = service.create(admin_user, "XYZ789", "Honda", "Civic", 2021, owner_id=client_user.id)

        assert result.owner_id == client_user.id

    def test_inspector_cannot_create_vehicle(self, db_session: Session):
        """Inspector cannot create vehicles."""
        auth_service = AuthService(db_session)
        inspector = auth_service.register_user(UserRegister(
            name="Inspector",
            email="inspector@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))

        service = VehicleService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.create(inspector, "ABC123", "Toyota", "Corolla", 2020)

        assert exc_info.value.status_code == 403

    def test_cannot_create_duplicate_plate(self, db_session: Session, client_user: User):
        """Cannot create vehicle with duplicate plate number."""
        service = VehicleService(db_session)
        service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        with pytest.raises(HTTPException) as exc_info:
            service.create(client_user, "ABC123", "Honda", "Civic", 2021)

        assert exc_info.value.status_code == 400


class TestVehicleServiceList:
    """Test the list service method."""

    @pytest.fixture
    def client_user(self, db_session: Session) -> User:
        """Create a client user."""
        auth_service = AuthService(db_session)
        return auth_service.register_user(UserRegister(
            name="Client User",
            email="client@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

    def test_client_sees_only_own_vehicles(self, db_session: Session, client_user: User):
        """Client sees only their own vehicles."""
        auth_service = AuthService(db_session)
        other_user = auth_service.register_user(UserRegister(
            name="Other User",
            email="other@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        vehicle_service = VehicleService(db_session)
        vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)
        vehicle_service.create(other_user, "XYZ789", "Honda", "Civic", 2021)

        vehicles, total = vehicle_service.list(client_user, page=1, page_size=10)

        assert total == 1
        assert vehicles[0].plate_number == "ABC123"

    def test_admin_sees_all_vehicles(self, db_session: Session, client_user: User):
        """Admin sees all vehicles."""
        auth_service = AuthService(db_session)
        admin = auth_service.register_user(UserRegister(
            name="Admin",
            email="admin@test.com",
            password="Password123",
            role=UserRole.ADMIN
        ))

        vehicle_service = VehicleService(db_session)
        vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)
        vehicle_service.create(client_user, "XYZ789", "Honda", "Civic", 2021)

        vehicles, total = vehicle_service.list(admin, page=1, page_size=10)

        assert total == 2

    def test_inspector_cannot_list_vehicles(self, db_session: Session):
        """Inspector cannot list vehicles."""
        auth_service = AuthService(db_session)
        inspector = auth_service.register_user(UserRegister(
            name="Inspector",
            email="inspector@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))

        service = VehicleService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.list(inspector, page=1, page_size=10)

        assert exc_info.value.status_code == 403

    def test_list_search_works(self, db_session: Session, client_user: User):
        """List search filter works."""
        vehicle_service = VehicleService(db_session)
        vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)
        vehicle_service.create(client_user, "XYZ789", "Honda", "Civic", 2021)

        vehicles, total = vehicle_service.list(client_user, page=1, page_size=10, search="Toyota")

        assert total == 1
        assert vehicles[0].make == "Toyota"


class TestVehicleServiceGet:
    """Test the get service method."""

    @pytest.fixture
    def client_user(self, db_session: Session) -> User:
        """Create a client user."""
        auth_service = AuthService(db_session)
        return auth_service.register_user(UserRegister(
            name="Client User",
            email="client@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

    def test_client_can_access_own_vehicle(self, db_session: Session, client_user: User):
        """Client can access their own vehicle."""
        vehicle_service = VehicleService(db_session)
        vehicle = vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        result = vehicle_service.get(vehicle.id, client_user)

        assert result.id == vehicle.id

    def test_client_cannot_access_other_vehicle(self, db_session: Session, client_user: User):
        """Client cannot access other user's vehicle."""
        auth_service = AuthService(db_session)
        other_user = auth_service.register_user(UserRegister(
            name="Other User",
            email="other@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        vehicle_service = VehicleService(db_session)
        vehicle = vehicle_service.create(other_user, "ABC123", "Toyota", "Corolla", 2020)

        with pytest.raises(HTTPException) as exc_info:
            vehicle_service.get(vehicle.id, client_user)

        assert exc_info.value.status_code == 403

    def test_inspector_can_access_any_vehicle(self, db_session: Session, client_user: User):
        """Inspector can access any vehicle."""
        auth_service = AuthService(db_session)
        inspector = auth_service.register_user(UserRegister(
            name="Inspector",
            email="inspector@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))

        vehicle_service = VehicleService(db_session)
        vehicle = vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        result = vehicle_service.get(vehicle.id, inspector)

        assert result.id == vehicle.id


class TestVehicleServiceGetByPlate:
    """Test the get_by_plate service method."""

    @pytest.fixture
    def client_user(self, db_session: Session) -> User:
        """Create a client user."""
        auth_service = AuthService(db_session)
        return auth_service.register_user(UserRegister(
            name="Client User",
            email="client@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

    def test_get_by_plate_works(self, db_session: Session, client_user: User):
        """Can get vehicle by plate number."""
        vehicle_service = VehicleService(db_session)
        vehicle = vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        result = vehicle_service.get_by_plate("ABC123", client_user)

        assert result.id == vehicle.id

    def test_get_by_plate_case_insensitive(self, db_session: Session, client_user: User):
        """Get by plate is case insensitive."""
        vehicle_service = VehicleService(db_session)
        vehicle = vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        result = vehicle_service.get_by_plate("abc123", client_user)

        assert result.id == vehicle.id


class TestVehicleServiceUpdate:
    """Test the update service method."""

    @pytest.fixture
    def client_user(self, db_session: Session) -> User:
        """Create a client user."""
        auth_service = AuthService(db_session)
        return auth_service.register_user(UserRegister(
            name="Client User",
            email="client@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

    def test_client_can_update_own_vehicle(self, db_session: Session, client_user: User):
        """Client can update their own vehicle."""
        vehicle_service = VehicleService(db_session)
        vehicle = vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        result = vehicle_service.update(vehicle.id, client_user, make="Honda")

        assert result.make == "Honda"

    def test_client_cannot_update_other_vehicle(self, db_session: Session, client_user: User):
        """Client cannot update other user's vehicle."""
        auth_service = AuthService(db_session)
        other_user = auth_service.register_user(UserRegister(
            name="Other User",
            email="other@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        vehicle_service = VehicleService(db_session)
        vehicle = vehicle_service.create(other_user, "ABC123", "Toyota", "Corolla", 2020)

        with pytest.raises(HTTPException) as exc_info:
            vehicle_service.update(vehicle.id, client_user, make="Honda")

        assert exc_info.value.status_code == 403

    def test_inspector_cannot_update_vehicles(self, db_session: Session, client_user: User):
        """Inspector cannot update vehicles."""
        auth_service = AuthService(db_session)
        inspector = auth_service.register_user(UserRegister(
            name="Inspector",
            email="inspector@test.com",
            password="Password123",
            role=UserRole.INSPECTOR
        ))

        vehicle_service = VehicleService(db_session)
        vehicle = vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        with pytest.raises(HTTPException) as exc_info:
            vehicle_service.update(vehicle.id, inspector, make="Honda")

        assert exc_info.value.status_code == 403


class TestVehicleServiceDelete:
    """Test the delete service method."""

    @pytest.fixture
    def client_user(self, db_session: Session) -> User:
        """Create a client user."""
        auth_service = AuthService(db_session)
        return auth_service.register_user(UserRegister(
            name="Client User",
            email="client@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

    def test_client_can_delete_own_vehicle_without_inspections(self, db_session: Session, client_user: User):
        """Client can delete their own vehicle if it has no inspections."""
        vehicle_service = VehicleService(db_session)
        vehicle = vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        vehicle_service.delete(vehicle.id, client_user)

        # Verify it was deleted
        assert db_session.query(Vehicle).filter(Vehicle.id == vehicle.id).first() is None

    def test_client_cannot_delete_vehicle_with_inspections(self, db_session: Session, client_user: User):
        """Client cannot delete vehicle with inspections."""
        vehicle_service = VehicleService(db_session)
        vehicle = vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        # Add an inspection
        inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=vehicle.id,
            year=2024,
            status="PENDING",
            attempt_count=0
        )
        db_session.add(inspection)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            vehicle_service.delete(vehicle.id, client_user)

        assert exc_info.value.status_code == 400

    def test_admin_can_delete_vehicle_with_inspections(self, db_session: Session, client_user: User):
        """Admin can delete vehicle even with inspections."""
        auth_service = AuthService(db_session)
        admin = auth_service.register_user(UserRegister(
            name="Admin",
            email="admin@test.com",
            password="Password123",
            role=UserRole.ADMIN
        ))

        vehicle_service = VehicleService(db_session)
        vehicle = vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        # Add an inspection
        inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=vehicle.id,
            year=2024,
            status="PENDING",
            attempt_count=0
        )
        db_session.add(inspection)
        db_session.commit()

        # Admin can still delete
        vehicle_service.delete(vehicle.id, admin)

        # Verify it was deleted
        assert db_session.query(Vehicle).filter(Vehicle.id == vehicle.id).first() is None
