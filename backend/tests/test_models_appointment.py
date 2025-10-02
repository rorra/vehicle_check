import pytest
from datetime import datetime, timedelta
from tests.conftest import utc_now
from app.models import (
    Appointment,
    AppointmentStatus,
    CreatedChannel,
    AnnualInspection,
    AnnualStatus,
    InspectionResult,
    AvailabilitySlot,
)


class TestAppointmentModel:
    def test_create_appointment(self, db_session, sample_vehicle, sample_inspector, sample_user):
        """Test creating an appointment."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )
        db_session.add(annual)
        db_session.commit()

        appointment_time = utc_now() + timedelta(days=7)
        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=appointment_time,
            status=AppointmentStatus.PENDING,
        )
        db_session.add(appointment)
        db_session.commit()

        retrieved = db_session.query(Appointment).filter_by(id="appointment-1").first()
        assert retrieved is not None
        assert retrieved.annual_inspection_id == annual.id
        assert retrieved.vehicle_id == sample_vehicle.id
        assert retrieved.inspector_id == sample_inspector.id
        assert retrieved.created_by_user_id == sample_user.id
        assert retrieved.created_channel == CreatedChannel.CLIENT_PORTAL
        assert retrieved.status == AppointmentStatus.PENDING

    def test_appointment_status_transitions(self, db_session, sample_vehicle, sample_inspector, sample_user):
        """Test appointment status transitions."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.PENDING,
        )
        db_session.add(appointment)
        db_session.commit()

        appointment.status = AppointmentStatus.CONFIRMED
        db_session.commit()
        assert appointment.status == AppointmentStatus.CONFIRMED

        appointment.status = AppointmentStatus.COMPLETED
        db_session.commit()
        assert appointment.status == AppointmentStatus.COMPLETED

    def test_appointment_created_channels(self, db_session, sample_vehicle, sample_inspector, sample_user):
        """Test different created channels."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )
        db_session.add(annual)
        db_session.commit()

        client_portal_appt = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.PENDING,
        )

        admin_panel_appt = Appointment(
            id="appointment-2",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.ADMIN_PANEL,
            date_time=utc_now() + timedelta(days=1),
            status=AppointmentStatus.PENDING,
        )

        db_session.add(client_portal_appt)
        db_session.add(admin_panel_appt)
        db_session.commit()

        assert client_portal_appt.created_channel == CreatedChannel.CLIENT_PORTAL
        assert admin_panel_appt.created_channel == CreatedChannel.ADMIN_PANEL

    def test_appointment_optional_inspector(self, db_session, sample_vehicle, sample_user):
        """Test that inspector assignment is optional."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=None,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.ADMIN_PANEL,
            date_time=utc_now(),
            status=AppointmentStatus.PENDING,
        )
        db_session.add(appointment)
        db_session.commit()

        retrieved = db_session.query(Appointment).filter_by(id="appointment-1").first()
        assert retrieved.inspector_id is None

    def test_appointment_confirmation_token(self, db_session, sample_vehicle, sample_inspector, sample_user):
        """Test appointment confirmation token."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.PENDING,
            confirmation_token="TOKEN-123",
        )
        db_session.add(appointment)
        db_session.commit()

        retrieved = db_session.query(Appointment).filter_by(id="appointment-1").first()
        assert retrieved.confirmation_token == "TOKEN-123"

    def test_appointment_cascade_delete(self, db_session, sample_vehicle, sample_inspector, sample_user):
        """Test that appointments are deleted when annual inspection is deleted."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.PENDING,
        )
        db_session.add(appointment)
        db_session.commit()

        db_session.delete(annual)
        db_session.commit()

        assert db_session.query(Appointment).filter_by(id="appointment-1").first() is None

    def test_appointment_repr(self, db_session, sample_vehicle, sample_inspector, sample_user):
        """Test appointment string representation."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.PENDING,
        )
        db_session.add(appointment)
        db_session.commit()

        repr_str = repr(appointment)
        assert "Appointment" in repr_str
        assert appointment.status.value in repr_str


class TestInspectionResultModel:
    def test_create_inspection_result(self, db_session, sample_vehicle, sample_inspector, sample_user):
        """Test creating an inspection result."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.IN_PROGRESS,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.COMPLETED,
        )
        db_session.add(appointment)
        db_session.commit()

        result = InspectionResult(
            id="result-1",
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=65,
            owner_observation=None,
        )
        db_session.add(result)
        db_session.commit()

        retrieved = db_session.query(InspectionResult).filter_by(id="result-1").first()
        assert retrieved is not None
        assert retrieved.annual_inspection_id == annual.id
        assert retrieved.appointment_id == appointment.id
        assert retrieved.total_score == 65
        assert retrieved.owner_observation is None

    def test_inspection_result_unique_appointment(self, db_session, sample_vehicle, sample_inspector, sample_user):
        """Test that each appointment can only have one inspection result."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.IN_PROGRESS,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.COMPLETED,
        )
        db_session.add(appointment)
        db_session.commit()

        result1 = InspectionResult(
            id="result-1",
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=60,
        )
        result2 = InspectionResult(
            id="result-2",
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=70,
        )

        db_session.add(result1)
        db_session.commit()

        db_session.add(result2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_inspection_result_with_observation(self, db_session, sample_vehicle, sample_inspector, sample_user):
        """Test inspection result with owner observation for low score."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.IN_PROGRESS,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.COMPLETED,
        )
        db_session.add(appointment)
        db_session.commit()

        result = InspectionResult(
            id="result-1",
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=35,
            owner_observation="El vehículo requiere reparaciones urgentes.",
        )
        db_session.add(result)
        db_session.commit()

        retrieved = db_session.query(InspectionResult).filter_by(id="result-1").first()
        assert retrieved.total_score == 35
        assert retrieved.owner_observation is not None

    def test_inspection_result_cascade_delete(self, db_session, sample_vehicle, sample_inspector, sample_user):
        """Test that inspection results are deleted when appointment is deleted."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.IN_PROGRESS,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.COMPLETED,
        )
        db_session.add(appointment)
        db_session.commit()

        result = InspectionResult(
            id="result-1",
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=65,
        )
        db_session.add(result)
        db_session.commit()

        db_session.delete(appointment)
        db_session.commit()

        assert db_session.query(InspectionResult).filter_by(id="result-1").first() is None

    def test_inspection_result_repr(self, db_session, sample_vehicle, sample_inspector, sample_user):
        """Test inspection result string representation."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.IN_PROGRESS,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.COMPLETED,
        )
        db_session.add(appointment)
        db_session.commit()

        result = InspectionResult(
            id="result-1",
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=65,
        )
        db_session.add(result)
        db_session.commit()

        repr_str = repr(result)
        assert "InspectionResult" in repr_str
        assert "65" in repr_str


class TestAvailabilitySlotModel:
    def test_create_availability_slot(self, db_session):
        """Test creating an availability slot."""
        start_time = utc_now()
        end_time = start_time + timedelta(hours=1)

        slot = AvailabilitySlot(
            id="slot-1",
            start_time=start_time,
            end_time=end_time,
            is_booked=False,
        )
        db_session.add(slot)
        db_session.commit()

        retrieved = db_session.query(AvailabilitySlot).filter_by(id="slot-1").first()
        assert retrieved is not None
        assert retrieved.is_booked is False

    def test_availability_slot_booking(self, db_session):
        """Test booking an availability slot."""
        start_time = utc_now()
        end_time = start_time + timedelta(hours=1)

        slot = AvailabilitySlot(
            id="slot-1",
            start_time=start_time,
            end_time=end_time,
            is_booked=False,
        )
        db_session.add(slot)
        db_session.commit()

        slot.is_booked = True
        db_session.commit()

        retrieved = db_session.query(AvailabilitySlot).filter_by(id="slot-1").first()
        assert retrieved.is_booked is True

    def test_availability_slot_repr(self, db_session):
        """Test availability slot string representation."""
        start_time = utc_now()
        end_time = start_time + timedelta(hours=1)

        slot = AvailabilitySlot(
            id="slot-1",
            start_time=start_time,
            end_time=end_time,
            is_booked=False,
        )
        db_session.add(slot)
        db_session.commit()

        repr_str = repr(slot)
        assert "AvailabilitySlot" in repr_str
        assert "booked" in repr_str
