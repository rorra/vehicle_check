import pytest
from app.models import Vehicle
from tests.factories import VehicleFactory


class TestVehicleRoutes:
    """Test vehicle HTTP endpoints (route→service wiring)."""

    def test_unauthenticated_request_fails(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/api/v1/vehicles/")
        assert response.status_code == 403

    def test_create_vehicle(self, client, client_user, client_token):
        """Test vehicle creation endpoint."""
        vehicle_data = {
            "plate_number": "ABC123",
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020
        }

        response = client.post(
            "/api/v1/vehicles/",
            json=vehicle_data,
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["plate_number"] == "ABC123"
        assert data["owner_id"] == client_user.id

    def test_list_vehicles_with_pagination(self, client, client_user, client_token, db_session):
        """Test vehicle listing with pagination."""
        # Create multiple vehicles
        for i in range(15):
            vehicle = VehicleFactory.build(
                id=f"vehicle-{i}",
                plate_number=f"TEST{i:03d}",
                owner_id=client_user.id
            )
            db_session.add(vehicle)
        db_session.commit()

        response = client.get(
            "/api/v1/vehicles/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 15
        assert len(data["vehicles"]) == 10
        assert data["page"] == 1

    def test_get_vehicle_by_id(self, client, client_user, client_token, db_session):
        """Test get vehicle by ID."""
        vehicle = VehicleFactory.build(
            id="test-vehicle",
            plate_number="TEST123",
            owner_id=client_user.id
        )
        db_session.add(vehicle)
        db_session.commit()

        response = client.get(
            "/api/v1/vehicles/test-vehicle",
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-vehicle"
        assert data["plate_number"] == "TEST123"

    def test_get_nonexistent_vehicle_returns_404(self, client, client_token):
        """Test that nonexistent vehicle returns 404."""
        response = client.get(
            "/api/v1/vehicles/nonexistent-id",
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 404

    def test_get_vehicle_by_plate(self, client, client_user, client_token, db_session):
        """Test get vehicle by plate number."""
        vehicle = VehicleFactory.build(
            id="test-vehicle",
            plate_number="PLATE123",
            owner_id=client_user.id
        )
        db_session.add(vehicle)
        db_session.commit()

        response = client.get(
            "/api/v1/vehicles/plate/PLATE123",
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200
        assert response.json()["plate_number"] == "PLATE123"

    def test_update_vehicle(self, client, client_user, client_token, db_session):
        """Test vehicle update."""
        vehicle = VehicleFactory.build(
            id="test-vehicle",
            plate_number="OLD123",
            owner_id=client_user.id
        )
        db_session.add(vehicle)
        db_session.commit()

        update_data = {"make": "Honda", "model": "Civic"}

        response = client.put(
            "/api/v1/vehicles/test-vehicle",
            json=update_data,
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["make"] == "Honda"
        assert data["model"] == "Civic"

    def test_delete_vehicle(self, client, client_user, client_token, db_session):
        """Test vehicle deletion."""
        vehicle = VehicleFactory.build(
            id="test-vehicle",
            plate_number="DELETE123",
            owner_id=client_user.id
        )
        db_session.add(vehicle)
        db_session.commit()

        response = client.delete(
            "/api/v1/vehicles/test-vehicle",
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200
        assert "eliminado exitosamente" in response.json()["message"]

    def test_get_vehicles_with_owners(self, client, client_user, admin_token, db_session):
        """Test admin endpoint for vehicles with owner details."""
        vehicle = VehicleFactory.build(
            id="test-vehicle",
            plate_number="TEST123",
            owner_id=client_user.id
        )
        db_session.add(vehicle)
        db_session.commit()

        response = client.get(
            "/api/v1/vehicles/with-owners",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        vehicle_data = next(v for v in data if v["id"] == "test-vehicle")
        assert vehicle_data["owner_name"] == "Client User"
