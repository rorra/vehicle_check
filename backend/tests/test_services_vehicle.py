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

    def test_create_vehicle_auto_creates_annual_inspection(self, db_session: Session, client_user: User):
        """Creating a vehicle automatically creates an annual inspection for current year."""
        from datetime import datetime
        service = VehicleService(db_session)
        result = service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        # Verify annual inspection was created
        annual_inspections = db_session.query(AnnualInspection).filter(
            AnnualInspection.vehicle_id == result.id
        ).all()

        assert len(annual_inspections) == 1
        assert annual_inspections[0].year == datetime.now().year
        assert annual_inspections[0].status.value == "PENDING"
        assert annual_inspections[0].attempt_count == 0

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

    def test_client_can_disable_vehicle(self, db_session: Session, client_user: User):
        """Client can disable their own vehicle (soft delete)."""
        vehicle_service = VehicleService(db_session)
        vehicle = vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        # Client "deletes" vehicle, which actually disables it
        vehicle_service.delete(vehicle.id, client_user)

        # Verify it was disabled, not deleted
        disabled_vehicle = db_session.query(Vehicle).filter(Vehicle.id == vehicle.id).first()
        assert disabled_vehicle is not None
        assert disabled_vehicle.is_active == False

    def test_disabled_vehicle_not_in_client_list(self, db_session: Session, client_user: User):
        """Disabled vehicles don't appear in client's vehicle list."""
        vehicle_service = VehicleService(db_session)
        vehicle1 = vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)
        vehicle2 = vehicle_service.create(client_user, "XYZ789", "Honda", "Civic", 2021)

        # Disable first vehicle
        vehicle_service.delete(vehicle1.id, client_user)

        # List should only show active vehicle
        vehicles, total = vehicle_service.list(client_user, page=1, page_size=10)
        assert total == 1
        assert vehicles[0].id == vehicle2.id

    def test_admin_can_see_disabled_vehicles_with_flag(self, db_session: Session, client_user: User):
        """Admin can see disabled vehicles when include_inactive=True."""
        auth_service = AuthService(db_session)
        admin = auth_service.register_user(UserRegister(
            name="Admin",
            email="admin@test.com",
            password="Password123",
            role=UserRole.ADMIN
        ))

        vehicle_service = VehicleService(db_session)
        vehicle = vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)

        # Client disables vehicle
        vehicle_service.delete(vehicle.id, client_user)

        # Admin can see it with include_inactive=True
        vehicles_inactive, total_inactive = vehicle_service.list(admin, page=1, page_size=10, include_inactive=True)
        assert total_inactive == 1
        assert vehicles_inactive[0].is_active == False

        # Admin doesn't see it by default
        vehicles_active, total_active = vehicle_service.list(admin, page=1, page_size=10, include_inactive=False)
        assert total_active == 0

    def test_creating_vehicle_with_disabled_plate_reassigns_it(self, db_session: Session, client_user: User):
        """Creating a vehicle with a disabled plate number reassigns and enables it."""
        auth_service = AuthService(db_session)
        new_owner = auth_service.register_user(UserRegister(
            name="New Owner",
            email="newowner@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        vehicle_service = VehicleService(db_session)

        # Client 1 creates and disables vehicle
        vehicle = vehicle_service.create(client_user, "ABC123", "Toyota", "Corolla", 2020)
        original_vehicle_id = vehicle.id
        vehicle_service.delete(vehicle.id, client_user)

        # Client 2 creates vehicle with same plate
        reassigned_vehicle = vehicle_service.create(new_owner, "ABC123", "Honda", "Accord", 2022)

        # Should be same vehicle ID, but reassigned to new owner
        assert reassigned_vehicle.id == original_vehicle_id
        assert reassigned_vehicle.owner_id == new_owner.id
        assert reassigned_vehicle.is_active == True
        assert reassigned_vehicle.make == "Honda"
        assert reassigned_vehicle.model == "Accord"
        assert reassigned_vehicle.year == 2022

        # New owner has access to previous annual inspections
        annual_inspections = db_session.query(AnnualInspection).filter(
            AnnualInspection.vehicle_id == reassigned_vehicle.id
        ).all()
        assert len(annual_inspections) >= 1  # At least the original one

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
