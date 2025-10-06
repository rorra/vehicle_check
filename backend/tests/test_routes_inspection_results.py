"""Tests for inspection result endpoints."""
import pytest
from datetime import datetime, timezone
from app.models import (
    User, Vehicle, AnnualInspection, Appointment, InspectionResult,
    Inspector, generate_uuid, AnnualStatus
)
from app.core.security import get_password_hash
from tests.factories import VehicleFactory, AnnualInspectionFactory


class TestInspectionResultRoutes:
    """Test inspection result HTTP endpoints."""

    def test_unauthenticated_request_fails(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/api/v1/inspection-results/")
        assert response.status_code == 403

    def test_list_inspection_results_with_pagination(self, client, db_session, client_token):
        """Test listing inspection results with pagination."""
        response = client.get(
            "/api/v1/inspection-results/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data
        assert data["page"] == 1

    def test_get_inspection_results_by_annual_inspection(
        self, client, client_user, client_token, db_session
    ):
        """Test get results by annual inspection ID."""
        vehicle = VehicleFactory.build(id="veh-1", owner_id=client_user.id)
        inspection = AnnualInspectionFactory.build(
            id="annual-1",
            vehicle_id=vehicle.id,
            year=2024,
            status=AnnualStatus.PENDING
        )
        db_session.add_all([vehicle, inspection])
        db_session.commit()

        response = client.get(
            "/api/v1/inspection-results/annual-inspection/annual-1",
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)
