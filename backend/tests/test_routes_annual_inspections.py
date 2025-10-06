"""Tests for annual inspection endpoints."""
import pytest
from app.models import User, Vehicle, AnnualInspection, generate_uuid, AnnualStatus, UserRole
from app.core.security import get_password_hash
from tests.factories import VehicleFactory, AnnualInspectionFactory, ClientUserFactory


class TestAnnualInspectionRoutes:
    """Test annual inspection HTTP endpoints."""

    def test_unauthenticated_request_fails(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/api/v1/annual-inspections/")
        assert response.status_code == 403

    def test_create_annual_inspection(self, client, client_user, client_token, db_session):
        """Test annual inspection creation."""
        vehicle = VehicleFactory.build(id="veh-1", owner_id=client_user.id)
        db_session.add(vehicle)
        db_session.commit()

        inspection_data = {
            "vehicle_id": vehicle.id,
            "year": 2024
        }

        response = client.post(
            "/api/v1/annual-inspections/",
            json=inspection_data,
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["vehicle_id"] == vehicle.id
        assert data["year"] == 2024
        assert data["status"] == "PENDING"

    def test_list_annual_inspections_with_pagination(self, client, db_session, client_token):
        """Test listing annual inspections with pagination."""
        user = ClientUserFactory.build(id="user-1")
        vehicle = VehicleFactory.build(id="veh-1", owner_id=user.id)
        inspection = AnnualInspectionFactory.build(
            id="insp-1",
            vehicle_id=vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING
        )
        db_session.add_all([user, vehicle, inspection])
        db_session.commit()

        response = client.get(
            "/api/v1/annual-inspections/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "inspections" in data
        assert "total" in data
        assert data["page"] == 1

    def test_get_annual_inspection_by_id(self, client, client_user, client_token, db_session):
        """Test get annual inspection by ID."""
        vehicle = VehicleFactory.build(id="veh-1", owner_id=client_user.id)
        inspection = AnnualInspectionFactory.build(
            id="test-inspection",
            vehicle_id=vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING
        )
        db_session.add_all([vehicle, inspection])
        db_session.commit()

        response = client.get(
            "/api/v1/annual-inspections/test-inspection",
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-inspection"
        assert data["year"] == 2024

    def test_update_annual_inspection(self, client, db_session, admin_token):
        """Test annual inspection update."""
        user = ClientUserFactory.build(id="user-1")
        vehicle = VehicleFactory.build(id="veh-1", owner_id=user.id)
        inspection = AnnualInspectionFactory.build(
            id="test-inspection",
            vehicle_id=vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING
        )
        db_session.add_all([user, vehicle, inspection])
        db_session.commit()

        update_data = {"status": "PASSED"}

        response = client.put(
            "/api/v1/annual-inspections/test-inspection",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PASSED"

    def test_delete_annual_inspection(self, client, db_session, admin_token):
        """Test annual inspection deletion."""
        user = ClientUserFactory.build(id="user-1")
        vehicle = VehicleFactory.build(id="veh-1", owner_id=user.id)
        inspection = AnnualInspectionFactory.build(
            id="test-inspection",
            vehicle_id=vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING
        )
        db_session.add_all([user, vehicle, inspection])
        db_session.commit()

        response = client.delete(
            "/api/v1/annual-inspections/test-inspection",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
