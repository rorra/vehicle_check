"""Tests for appointment endpoints."""
import pytest
from datetime import datetime, timezone
from app.models import User, Vehicle, AnnualInspection, Appointment, Inspector, generate_uuid, AnnualStatus, AppointmentStatus, CreatedChannel
from app.core.security import get_password_hash
from tests.factories import VehicleFactory, AnnualInspectionFactory, AppointmentFactory


class TestAppointmentRoutes:
    """Test appointment HTTP endpoints."""

    def test_unauthenticated_request_fails(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/api/v1/appointments/")
        assert response.status_code == 403

    def test_list_appointments_with_pagination(self, client, db_session, client_token):
        """Test listing appointments with pagination."""
        response = client.get(
            "/api/v1/appointments/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "appointments" in data
        assert "total" in data
        assert data["page"] == 1

    def test_get_appointment_by_id(self, client, client_user, client_token, db_session):
        """Test get appointment by ID."""
        vehicle = VehicleFactory.build(id="veh-1", owner_id=client_user.id)
        inspection = AnnualInspectionFactory.build(
            id="insp-1",
            vehicle_id=vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING
        )
        appointment = AppointmentFactory.build(
            id="appt-1",
            annual_inspection_id=inspection.id,
            vehicle_id=vehicle.id,
            created_by_user_id=client_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=datetime.now(timezone.utc),
            status=AppointmentStatus.CONFIRMED
        )
        db_session.add_all([vehicle, inspection, appointment])
        db_session.commit()

        response = client.get(
            "/api/v1/appointments/appt-1",
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "appt-1"

    def test_cancel_appointment(self, client, client_user, admin_token, db_session):
        """Test appointment cancellation."""
        vehicle = VehicleFactory.build(id="veh-1", owner_id=client_user.id)
        inspection = AnnualInspectionFactory.build(
            id="insp-1",
            vehicle_id=vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING
        )
        appointment = AppointmentFactory.build(
            id="appt-1",
            annual_inspection_id=inspection.id,
            vehicle_id=vehicle.id,
            created_by_user_id=client_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=datetime.now(timezone.utc),
            status=AppointmentStatus.CONFIRMED
        )
        db_session.add_all([vehicle, inspection, appointment])
        db_session.commit()

        response = client.delete(
            "/api/v1/appointments/appt-1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
