import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.annual_inspection_service import AnnualInspectionService
from app.models import (
    User,
    UserRole,
    Vehicle,
    AnnualInspection,
    AnnualStatus,
    Appointment,
    AppointmentStatus,
    CreatedChannel,
    Inspector,
    generate_uuid,
)
from app.schemas.annual_inspection import (
    AnnualInspectionCreate,
    AnnualInspectionUpdate,
)


class TestAnnualInspectionServiceCreate:
    """Test the create service method."""

    def test_client_can_create_for_own_vehicle(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle
    ):
        """Client can create annual inspection for their own vehicle."""
        service = AnnualInspectionService(db_session)
        data = AnnualInspectionCreate(
            vehicle_id=client_vehicle.id,
            year=datetime.now().year
        )

        result = service.create(data, client_user)

        assert result.vehicle_id == client_vehicle.id
        assert result.year == datetime.now().year
        assert result.status == AnnualStatus.PENDING
        assert result.attempt_count == 0

    def test_admin_can_create_for_any_vehicle(
        self,
        db_session: Session,
        admin_user: User,
        client_vehicle: Vehicle
    ):
        """Admin can create annual inspection for any vehicle."""
        service = AnnualInspectionService(db_session)
        data = AnnualInspectionCreate(
            vehicle_id=client_vehicle.id,
            year=datetime.now().year
        )

        result = service.create(data, admin_user)

        assert result.vehicle_id == client_vehicle.id
        assert result.status == AnnualStatus.PENDING

    def test_inspector_cannot_create(
        self,
        db_session: Session,
        inspector_user: User,
        client_vehicle: Vehicle
    ):
        """Inspector cannot create annual inspections."""
        service = AnnualInspectionService(db_session)
        data = AnnualInspectionCreate(
            vehicle_id=client_vehicle.id,
            year=datetime.now().year
        )

        with pytest.raises(HTTPException) as exc_info:
            service.create(data, inspector_user)

        assert exc_info.value.status_code == 403
        assert "inspectores no pueden crear" in exc_info.value.detail.lower()

    def test_client_cannot_create_for_other_vehicle(
        self,
        db_session: Session,
        client_user: User,
        sample_user: User
    ):
        """Client cannot create inspection for other user's vehicle."""
        # Create vehicle owned by sample_user
        other_vehicle = Vehicle(
            id=generate_uuid(),
            plate_number=f"OTHER-{generate_uuid()[:8]}",
            owner_id=sample_user.id,
            make="Honda",
            model="Civic",
            year=2021,
        )
        db_session.add(other_vehicle)
        db_session.commit()

        service = AnnualInspectionService(db_session)
        data = AnnualInspectionCreate(
            vehicle_id=other_vehicle.id,
            year=datetime.now().year
        )

        with pytest.raises(HTTPException) as exc_info:
            service.create(data, client_user)

        assert exc_info.value.status_code == 403
        assert "no tienes permisos" in exc_info.value.detail.lower()

    def test_cannot_create_for_nonexistent_vehicle(
        self,
        db_session: Session,
        client_user: User
    ):
        """Cannot create inspection for non-existent vehicle."""
        service = AnnualInspectionService(db_session)
        data = AnnualInspectionCreate(
            vehicle_id=generate_uuid(),
            year=datetime.now().year
        )

        with pytest.raises(HTTPException) as exc_info:
            service.create(data, client_user)

        assert exc_info.value.status_code == 404
        assert "vehículo no encontrado" in exc_info.value.detail.lower()

    def test_cannot_create_duplicate(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle
    ):
        """Cannot create duplicate inspection for same vehicle and year."""
        # Create first inspection
        service = AnnualInspectionService(db_session)
        data = AnnualInspectionCreate(
            vehicle_id=client_vehicle.id,
            year=datetime.now().year
        )
        service.create(data, client_user)

        # Try to create duplicate
        with pytest.raises(HTTPException) as exc_info:
            service.create(data, client_user)

        assert exc_info.value.status_code == 400
        assert "ya existe" in exc_info.value.detail.lower()


class TestAnnualInspectionServiceList:
    """Test the list service method."""

    def test_client_sees_only_own_inspections(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle,
        sample_user: User
    ):
        """Client can only see inspections for their own vehicles."""
        # Create inspection for client
        client_inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(client_inspection)

        # Create vehicle and inspection for another user
        other_vehicle = Vehicle(
            id=generate_uuid(),
            plate_number=f"OTHER-{generate_uuid()[:8]}",
            owner_id=sample_user.id,
            make="Honda",
            model="Civic",
            year=2021,
        )
        db_session.add(other_vehicle)
        db_session.commit()

        other_inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=other_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(other_inspection)
        db_session.commit()

        service = AnnualInspectionService(db_session)
        inspections, total = service.list(client_user)

        assert total == 1
        assert len(inspections) == 1
        assert inspections[0].id == client_inspection.id

    def test_admin_sees_all_inspections(
        self,
        db_session: Session,
        admin_user: User,
        client_vehicle: Vehicle,
        sample_user: User
    ):
        """Admin can see all inspections."""
        # Create inspection for client
        client_inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(client_inspection)

        # Create vehicle and inspection for another user
        other_vehicle = Vehicle(
            id=generate_uuid(),
            plate_number=f"OTHER-{generate_uuid()[:8]}",
            owner_id=sample_user.id,
            make="Honda",
            model="Civic",
            year=2021,
        )
        db_session.add(other_vehicle)
        db_session.commit()

        other_inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=other_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(other_inspection)
        db_session.commit()

        service = AnnualInspectionService(db_session)
        inspections, total = service.list(admin_user)

        assert total == 2
        assert len(inspections) == 2

    def test_filter_by_status(
        self,
        db_session: Session,
        admin_user: User,
        client_vehicle: Vehicle
    ):
        """Can filter inspections by status."""
        # Create pending inspection
        pending = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(pending)

        # Create passed inspection
        passed = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=2023,
            status=AnnualStatus.PASSED,
            attempt_count=1,
        )
        db_session.add(passed)
        db_session.commit()

        service = AnnualInspectionService(db_session)
        inspections, total = service.list(admin_user, status_filter=AnnualStatus.PENDING)

        assert total == 1
        assert inspections[0].status == AnnualStatus.PENDING

    def test_filter_by_year(
        self,
        db_session: Session,
        admin_user: User,
        client_vehicle: Vehicle
    ):
        """Can filter inspections by year."""
        # Create inspections for different years
        inspection_2024 = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(inspection_2024)

        inspection_2023 = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=2023,
            status=AnnualStatus.PASSED,
            attempt_count=1,
        )
        db_session.add(inspection_2023)
        db_session.commit()

        service = AnnualInspectionService(db_session)
        inspections, total = service.list(admin_user, year=2024)

        assert total == 1
        assert inspections[0].year == 2024

    def test_pagination_works(
        self,
        db_session: Session,
        admin_user: User,
        client_vehicle: Vehicle
    ):
        """Pagination works correctly."""
        # Create 5 inspections
        for i in range(5):
            inspection = AnnualInspection(
                id=generate_uuid(),
                vehicle_id=client_vehicle.id,
                year=2020 + i,
                status=AnnualStatus.PENDING,
                attempt_count=0,
            )
            db_session.add(inspection)
        db_session.commit()

        service = AnnualInspectionService(db_session)

        # Get first page (2 items)
        inspections, total = service.list(admin_user, page=1, page_size=2)
        assert total == 5
        assert len(inspections) == 2

        # Get second page (2 items)
        inspections, total = service.list(admin_user, page=2, page_size=2)
        assert total == 5
        assert len(inspections) == 2


class TestAnnualInspectionServiceGet:
    """Test the get service method."""

    def test_client_can_access_own_inspection(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle
    ):
        """Client can access inspection for their own vehicle."""
        inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(inspection)
        db_session.commit()

        service = AnnualInspectionService(db_session)
        result = service.get(inspection.id, client_user)

        assert result.id == inspection.id

    def test_client_cannot_access_other_inspection(
        self,
        db_session: Session,
        client_user: User,
        sample_user: User
    ):
        """Client cannot access inspection for other user's vehicle."""
        # Create vehicle for another user
        other_vehicle = Vehicle(
            id=generate_uuid(),
            plate_number=f"OTHER-{generate_uuid()[:8]}",
            owner_id=sample_user.id,
            make="Honda",
            model="Civic",
            year=2021,
        )
        db_session.add(other_vehicle)
        db_session.commit()

        inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=other_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(inspection)
        db_session.commit()

        service = AnnualInspectionService(db_session)
        with pytest.raises(HTTPException) as exc_info:
            service.get(inspection.id, client_user)

        assert exc_info.value.status_code == 403

    def test_admin_can_access_any_inspection(
        self,
        db_session: Session,
        admin_user: User,
        client_vehicle: Vehicle
    ):
        """Admin can access any inspection."""
        inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(inspection)
        db_session.commit()

        service = AnnualInspectionService(db_session)
        result = service.get(inspection.id, admin_user)

        assert result.id == inspection.id

    def test_get_nonexistent_inspection(
        self,
        db_session: Session,
        admin_user: User
    ):
        """Raises error when inspection doesn't exist."""
        service = AnnualInspectionService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.get(generate_uuid(), admin_user)

        assert exc_info.value.status_code == 404


class TestAnnualInspectionServiceUpdate:
    """Test the update service method."""

    def test_can_update_status(
        self,
        db_session: Session,
        admin_user: User,
        client_vehicle: Vehicle
    ):
        """Can update inspection status."""
        inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(inspection)
        db_session.commit()

        service = AnnualInspectionService(db_session)
        data = AnnualInspectionUpdate(status=AnnualStatus.PASSED)
        result = service.update(inspection.id, data, admin_user)

        assert result.status == AnnualStatus.PASSED

    def test_update_nonexistent_inspection(
        self,
        db_session: Session,
        admin_user: User
    ):
        """Raises error when updating non-existent inspection."""
        service = AnnualInspectionService(db_session)
        data = AnnualInspectionUpdate(status=AnnualStatus.PASSED)

        with pytest.raises(HTTPException) as exc_info:
            service.update(generate_uuid(), data, admin_user)

        assert exc_info.value.status_code == 404


class TestAnnualInspectionServiceDelete:
    """Test the delete service method."""

    def test_can_delete_inspection(
        self,
        db_session: Session,
        admin_user: User,
        client_vehicle: Vehicle
    ):
        """Can delete an inspection."""
        inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(inspection)
        db_session.commit()

        service = AnnualInspectionService(db_session)
        service.delete(inspection.id, admin_user)

        # Verify deleted
        deleted = db_session.query(AnnualInspection).filter(
            AnnualInspection.id == inspection.id
        ).first()
        assert deleted is None

    def test_delete_nonexistent_inspection(
        self,
        db_session: Session,
        admin_user: User
    ):
        """Raises error when deleting non-existent inspection."""
        service = AnnualInspectionService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.delete(generate_uuid(), admin_user)

        assert exc_info.value.status_code == 404


class TestAnnualInspectionServiceGetAppointmentStatistics:
    """Test the get_appointment_statistics service method."""

    def test_returns_statistics_with_appointments(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle,
        sample_inspector: Inspector
    ):
        """Returns correct statistics when appointments exist."""
        # Create annual inspection
        inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(inspection)
        db_session.commit()

        # Create 3 appointments
        for i in range(3):
            appointment = Appointment(
                id=generate_uuid(),
                annual_inspection_id=inspection.id,
                vehicle_id=client_vehicle.id,
                inspector_id=sample_inspector.id,
                created_by_user_id=client_user.id,
                created_channel=CreatedChannel.CLIENT_PORTAL,
                date_time=datetime.now(timezone.utc) + timedelta(days=i),
                status=AppointmentStatus.CONFIRMED,
                confirmation_token=f"CONF-{generate_uuid()[:8]}",
            )
            db_session.add(appointment)
        db_session.commit()

        service = AnnualInspectionService(db_session)
        stats = service.get_appointment_statistics(inspection.id)

        assert stats["total_appointments"] == 3
        assert stats["last_appointment_date"] is not None

    def test_returns_zero_when_no_appointments(
        self,
        db_session: Session,
        client_vehicle: Vehicle
    ):
        """Returns zero count when no appointments exist."""
        # Create annual inspection without appointments
        inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(inspection)
        db_session.commit()

        service = AnnualInspectionService(db_session)
        stats = service.get_appointment_statistics(inspection.id)

        assert stats["total_appointments"] == 0
        assert stats["last_appointment_date"] is None
