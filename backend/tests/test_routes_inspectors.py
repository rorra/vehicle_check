"""Tests for inspector endpoints."""
import pytest
from app.models import User, Inspector, generate_uuid
from app.core.security import get_password_hash


class TestInspectorRoutes:
    """Test inspector HTTP endpoints."""

    def test_unauthenticated_request_fails(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/api/v1/inspectors/")
        assert response.status_code == 403

    def test_create_inspector(self, client, db_session, admin_token):
        """Test inspector creation."""
        # Create inspector user
        user = User(
            id="inspector-user-id",
            name="Inspector User",
            email="inspector@example.com",
            password_hash=get_password_hash("password123"),
            role="INSPECTOR",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        inspector_data = {
            "user_id": user.id,
            "employee_id": "EMP001"
        }

        response = client.post(
            "/api/v1/inspectors/",
            json=inspector_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["employee_id"] == "EMP001"
        assert data["user_id"] == user.id

    def test_list_inspectors(self, client, db_session, admin_token):
        """Test listing inspectors with pagination."""
        # Create inspector
        user = User(
            id="inspector-user",
            name="Inspector",
            email="insp@test.com",
            password_hash=get_password_hash("pass"),
            role="INSPECTOR"
        )
        inspector = Inspector(
            id="insp-1",
            user_id=user.id,
            employee_id="EMP001",
            active=True
        )
        db_session.add_all([user, inspector])
        db_session.commit()

        response = client.get(
            "/api/v1/inspectors/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "inspectors" in data
        assert "total" in data

    def test_get_inspector_by_id(self, client, db_session, admin_token):
        """Test get inspector by ID."""
        user = User(
            id="inspector-user",
            name="Inspector",
            email="insp@test.com",
            password_hash=get_password_hash("pass"),
            role="INSPECTOR"
        )
        inspector = Inspector(
            id="test-inspector",
            user_id=user.id,
            employee_id="EMP001"
        )
        db_session.add_all([user, inspector])
        db_session.commit()

        response = client.get(
            "/api/v1/inspectors/test-inspector",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-inspector"
        assert data["employee_id"] == "EMP001"

    def test_update_inspector(self, client, db_session, admin_token):
        """Test inspector update."""
        user = User(
            id="inspector-user",
            name="Inspector",
            email="insp@test.com",
            password_hash=get_password_hash("pass"),
            role="INSPECTOR"
        )
        inspector = Inspector(
            id="test-inspector",
            user_id=user.id,
            employee_id="EMP001"
        )
        db_session.add_all([user, inspector])
        db_session.commit()

        update_data = {"employee_id": "EMP002"}

        response = client.put(
            "/api/v1/inspectors/test-inspector",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["employee_id"] == "EMP002"

    def test_delete_inspector(self, client, db_session, admin_token):
        """Test inspector deletion."""
        user = User(
            id="inspector-user",
            name="Inspector",
            email="insp@test.com",
            password_hash=get_password_hash("pass"),
            role="INSPECTOR"
        )
        inspector = Inspector(
            id="test-inspector",
            user_id=user.id,
            employee_id="EMP001"
        )
        db_session.add_all([user, inspector])
        db_session.commit()

        response = client.delete(
            "/api/v1/inspectors/test-inspector",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
