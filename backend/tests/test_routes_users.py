"""Tests for user endpoints."""
import pytest
from app.models import User
from app.core.security import get_password_hash


class TestUserRoutes:
    """Test user HTTP endpoints."""

    def test_unauthenticated_request_fails(self, client):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 403

    def test_get_current_user(self, client, db_session, client_user, client_token):
        """Test get current user profile."""
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == client_user.email
        assert "password_hash" not in data

    def test_update_current_user(self, client, client_token):
        """Test update current user profile."""
        update_data = {"name": "Updated Name"}

        response = client.put(
            "/api/v1/users/me",
            json=update_data,
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_change_password(self, client, client_user, client_token):
        """Test password change."""
        password_data = {
            "current_password": "password",  # Match conftest password
            "new_password": "newpassword456"
        }

        response = client.post(
            "/api/v1/users/me/change-password",
            json=password_data,
            headers={"Authorization": f"Bearer {client_token}"}
        )

        assert response.status_code == 200

    def test_admin_create_user(self, client, admin_token):
        """Test admin creating new user."""
        user_data = {
            "name": "New User",
            "email": "newuser@example.com",
            "password": "password123",
            "role": "CLIENT"
        }

        response = client.post(
            "/api/v1/users/",
            json=user_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New User"
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "CLIENT"
        assert "password" not in data
        assert "password_hash" not in data

    def test_admin_list_users(self, client, db_session, admin_token):
        """Test admin listing users with pagination."""
        response = client.get(
            "/api/v1/users/?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert data["page"] == 1

    def test_admin_get_user_by_id(self, client, db_session, admin_token):
        """Test admin get user by ID."""
        user = User(
            id="test-user",
            name="Test User",
            email="test@example.com",
            password_hash=get_password_hash("pass"),
            role="CLIENT"
        )
        db_session.add(user)
        db_session.commit()

        response = client.get(
            "/api/v1/users/test-user",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-user"

    def test_admin_update_user(self, client, db_session, admin_token):
        """Test admin updating user."""
        user = User(
            id="test-user",
            name="Test User",
            email="test@example.com",
            password_hash=get_password_hash("pass"),
            role="CLIENT"
        )
        db_session.add(user)
        db_session.commit()

        update_data = {"name": "Updated Name", "role": "INSPECTOR"}

        response = client.put(
            "/api/v1/users/test-user",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_admin_delete_user(self, client, db_session, admin_token):
        """Test admin deleting user."""
        user = User(
            id="test-user",
            name="Test User",
            email="test@example.com",
            password_hash=get_password_hash("pass"),
            role="CLIENT"
        )
        db_session.add(user)
        db_session.commit()

        response = client.delete(
            "/api/v1/users/test-user",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == 200
