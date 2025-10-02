import pytest
from datetime import datetime
from app.models import Vehicle, AnnualInspection, AnnualStatus


class TestVehicleModel:
    def test_create_vehicle(self, db_session, sample_user):
        """Test creating a vehicle."""
        vehicle = Vehicle(
            id="vehicle-1",
            plate_number="XYZ789",
            make="Honda",
            model="Civic",
            year=2019,
            owner_id=sample_user.id,
        )
        db_session.add(vehicle)
        db_session.commit()

        retrieved = db_session.query(Vehicle).filter_by(id="vehicle-1").first()
        assert retrieved is not None
        assert retrieved.plate_number == "XYZ789"
        assert retrieved.make == "Honda"
        assert retrieved.model == "Civic"
        assert retrieved.year == 2019
        assert retrieved.owner_id == sample_user.id

    def test_vehicle_unique_plate_number(self, db_session, sample_user):
        """Test that plate numbers must be unique."""
        vehicle1 = Vehicle(
            id="vehicle-1",
            plate_number="DUPLICATE",
            make="Toyota",
            model="Corolla",
            year=2020,
            owner_id=sample_user.id,
        )
        vehicle2 = Vehicle(
            id="vehicle-2",
            plate_number="DUPLICATE",
            make="Honda",
            model="Civic",
            year=2021,
            owner_id=sample_user.id,
        )

        db_session.add(vehicle1)
        db_session.commit()

        db_session.add(vehicle2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_vehicle_optional_fields(self, db_session, sample_user):
        """Test that make, model, and year are optional."""
        vehicle = Vehicle(
            id="vehicle-1",
            plate_number="ABC123",
            owner_id=sample_user.id,
        )
        db_session.add(vehicle)
        db_session.commit()

        retrieved = db_session.query(Vehicle).filter_by(id="vehicle-1").first()
        assert retrieved is not None
        assert retrieved.make is None
        assert retrieved.model is None
        assert retrieved.year is None

    def test_vehicle_owner_relationship(self, db_session, sample_user):
        """Test relationship between vehicle and owner."""
        vehicle = Vehicle(
            id="vehicle-1",
            plate_number="ABC123",
            make="Toyota",
            model="Corolla",
            year=2020,
            owner_id=sample_user.id,
        )
        db_session.add(vehicle)
        db_session.commit()

        retrieved = db_session.query(Vehicle).filter_by(id="vehicle-1").first()
        assert retrieved.owner is not None
        assert retrieved.owner.id == sample_user.id
        assert retrieved.owner.email == sample_user.email

    def test_vehicle_repr(self, sample_vehicle):
        """Test vehicle string representation."""
        repr_str = repr(sample_vehicle)
        assert "Vehicle" in repr_str
        assert sample_vehicle.plate_number in repr_str


class TestAnnualInspectionModel:
    def test_create_annual_inspection(self, db_session, sample_vehicle):
        """Test creating an annual inspection."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()

        retrieved = db_session.query(AnnualInspection).filter_by(id="annual-1").first()
        assert retrieved is not None
        assert retrieved.vehicle_id == sample_vehicle.id
        assert retrieved.year == 2024
        assert retrieved.status == AnnualStatus.PENDING
        assert retrieved.attempt_count == 0

    def test_annual_inspection_unique_vehicle_year(self, db_session, sample_vehicle):
        """Test that each vehicle can only have one inspection per year."""
        annual1 = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )
        annual2 = AnnualInspection(
            id="annual-2",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )

        db_session.add(annual1)
        db_session.commit()

        db_session.add(annual2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_annual_inspection_different_years(self, db_session, sample_vehicle):
        """Test that a vehicle can have inspections in different years."""
        annual_2023 = AnnualInspection(
            id="annual-2023",
            vehicle_id=sample_vehicle.id,
            year=2023,
            status=AnnualStatus.PASSED,
        )
        annual_2024 = AnnualInspection(
            id="annual-2024",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )

        db_session.add(annual_2023)
        db_session.add(annual_2024)
        db_session.commit()

        assert db_session.query(AnnualInspection).filter_by(vehicle_id=sample_vehicle.id).count() == 2

    def test_annual_inspection_status_transitions(self, db_session, sample_vehicle):
        """Test status transitions for annual inspections."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )
        db_session.add(annual)
        db_session.commit()

        annual.status = AnnualStatus.IN_PROGRESS
        db_session.commit()
        assert annual.status == AnnualStatus.IN_PROGRESS

        annual.status = AnnualStatus.PASSED
        db_session.commit()
        assert annual.status == AnnualStatus.PASSED

    def test_annual_inspection_attempt_count(self, db_session, sample_vehicle):
        """Test tracking inspection attempts."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()

        annual.attempt_count = 1
        db_session.commit()

        retrieved = db_session.query(AnnualInspection).filter_by(id="annual-1").first()
        assert retrieved.attempt_count == 1

        annual.attempt_count = 2
        db_session.commit()

        retrieved = db_session.query(AnnualInspection).filter_by(id="annual-1").first()
        assert retrieved.attempt_count == 2

    def test_annual_inspection_vehicle_relationship(self, db_session, sample_vehicle):
        """Test relationship between annual inspection and vehicle."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )
        db_session.add(annual)
        db_session.commit()

        retrieved = db_session.query(AnnualInspection).filter_by(id="annual-1").first()
        assert retrieved.vehicle is not None
        assert retrieved.vehicle.id == sample_vehicle.id
        assert retrieved.vehicle.plate_number == sample_vehicle.plate_number

    def test_annual_inspection_cascade_delete(self, db_session, sample_vehicle):
        """Test that annual inspections are deleted when vehicle is deleted."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )
        db_session.add(annual)
        db_session.commit()

        db_session.delete(sample_vehicle)
        db_session.commit()

        assert db_session.query(AnnualInspection).filter_by(id="annual-1").first() is None

    def test_annual_inspection_repr(self, db_session, sample_vehicle):
        """Test annual inspection string representation."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )
        db_session.add(annual)
        db_session.commit()

        repr_str = repr(annual)
        assert "AnnualInspection" in repr_str
        assert str(annual.year) in repr_str
        assert annual.status.value in repr_str
