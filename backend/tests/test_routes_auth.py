"""Tests for authentication endpoints."""
import pytest
from datetime import datetime, timezone, timedelta
from app.models import User, UserSession
from app.core.security import get_password_hash, create_access_token


class TestAuthRoutes:
    """Test authentication HTTP endpoints."""

    def test_register_user(self, client, db_session):
        """Test user registration."""
        user_data = {
            "name": "Test User",
            "email": "newuser@example.com",
            "password": "password123",
            "role": "CLIENT"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "CLIENT"
        assert "password" not in data

    def test_register_duplicate_email_fails(self, client, db_session):
        """Test that duplicate email registration fails."""
        user = User(
            id="existing-user",
            name="Existing",
            email="existing@example.com",
            password_hash=get_password_hash("password"),
            role="CLIENT"
        )
        db_session.add(user)
        db_session.commit()

        user_data = {
            "name": "New User",
            "email": "existing@example.com",
            "password": "password123"
        }

        response = client.post("/api/v1/auth/register", json=user_data)

        assert response.status_code == 400

    def test_login_returns_token(self, client, db_session):
        """Test login returns access token."""
        user = User(
            id="test-user",
            name="Test User",
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            role="CLIENT",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password_fails(self, client, db_session):
        """Test login with wrong password fails."""
        user = User(
            id="test-user",
            name="Test User",
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            role="CLIENT"
        )
        db_session.add(user)
        db_session.commit()

        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }

        response = client.post("/api/v1/auth/login", json=login_data)

        assert response.status_code == 401

    def test_logout_revokes_session(self, client, db_session):
        """Test logout revokes the session."""
        user = User(
            id="test-user",
            name="Test User",
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            role="CLIENT",
            is_active=True
        )
        db_session.add(user)
        db_session.commit()

        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]

        # Logout
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200

        # Verify token is revoked
        response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401

    def test_forgot_password_endpoint(self, client, db_session, monkeypatch):
        """Test forgot password endpoint."""
        user = User(
            id="test-user",
            name="Test User",
            email="test@example.com",
            password_hash=get_password_hash("password123"),
            role="CLIENT"
        )
        db_session.add(user)
        db_session.commit()

        # Mock email sending
        def mock_send_email(*args, **kwargs):
            pass

        from app.services import auth_service
        monkeypatch.setattr(auth_service, "send_password_reset_email", mock_send_email)

        response = client.post("/api/v1/auth/forgot-password", json={
            "email": "test@example.com"
        })

        assert response.status_code == 200
