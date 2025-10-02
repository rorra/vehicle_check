import pytest
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.models import User, UserRole


@pytest.fixture
def app():
    """Create a test FastAPI app with logging middleware."""
    test_app = FastAPI()

    # Add a simple middleware to set user before logging middleware
    from starlette.middleware.base import BaseHTTPMiddleware

    class UserMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if request.url.path == "/test-with-user":
                # Simulate authenticated user
                user = User(
                    id="test-user-id",
                    name="Test User",
                    email="test@example.com",
                    role=UserRole.CLIENT,
                    password_hash="hash"
                )
                request.state.user = user
            response = await call_next(request)
            return response

    # Add middlewares in order (reverse execution order)
    test_app.add_middleware(RequestLoggingMiddleware)
    test_app.add_middleware(UserMiddleware)

    @test_app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    @test_app.get("/test-with-user")
    async def test_with_user():
        return {"message": "authenticated"}

    @test_app.get("/test-error")
    async def test_error():
        raise HTTPException(status_code=400, detail="Bad request")

    @test_app.get("/test-server-error")
    async def test_server_error():
        raise HTTPException(status_code=500, detail="Server error")

    @test_app.get("/docs")
    async def test_docs():
        return {"message": "docs"}

    @test_app.post("/test-post")
    async def test_post(data: dict):
        return data

    return test_app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def caplog_fixture(caplog):
    """Configure caplog to capture all log levels."""
    caplog.set_level(logging.DEBUG)
    return caplog


class TestRequestLoggingMiddleware:
    """Tests for RequestLoggingMiddleware."""

    def test_logs_successful_request(self, client, caplog_fixture):
        """Test that successful requests are logged."""
        response = client.get("/test")

        assert response.status_code == 200

        # Check logs contain request and response
        log_messages = [record.message for record in caplog_fixture.records]
        assert any("→ GET /test" in msg for msg in log_messages)
        assert any("✓ GET /test - 200" in msg for msg in log_messages)

    def test_adds_request_id_header(self, client):
        """Test that X-Request-ID header is added to response."""
        response = client.get("/test")

        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 36  # UUID length

    def test_logs_request_with_user_info(self, client, caplog_fixture):
        """Test that authenticated user info is logged in response."""
        response = client.get("/test-with-user")

        assert response.status_code == 200

        # Check that user info is in log records (should be in response log)
        # Filter only middleware logs
        middleware_records = [r for r in caplog_fixture.records if r.name == "app.middleware.logging_middleware"]

        user_info_found = False
        for record in middleware_records:
            if hasattr(record, 'user_id') and record.user_id == "test-user-id":
                assert record.user_email == "test@example.com"
                assert "UserRole.CLIENT" in record.user_role
                user_info_found = True
                break

        assert user_info_found, "User info not found in middleware logs"

    def test_logs_client_error(self, client, caplog_fixture):
        """Test that client errors (4xx) are logged with warning level."""
        response = client.get("/test-error")

        assert response.status_code == 400

        # Check warning log
        log_messages = [record.message for record in caplog_fixture.records]
        assert any("✗ GET /test-error - 400" in msg for msg in log_messages)

        # Check log level is WARNING for 4xx
        warning_logs = [r for r in caplog_fixture.records if r.levelname == "WARNING"]
        assert any("/test-error" in r.message for r in warning_logs)

    def test_logs_server_error(self, client, caplog_fixture):
        """Test that server errors (5xx) are logged with error level."""
        response = client.get("/test-server-error")

        assert response.status_code == 500

        # Check error log
        log_messages = [record.message for record in caplog_fixture.records]
        assert any("✗ GET /test-server-error - 500" in msg for msg in log_messages)

        # Check log level is ERROR for 5xx
        error_logs = [r for r in caplog_fixture.records if r.levelname == "ERROR"]
        assert any("/test-server-error" in r.message for r in error_logs)

    def test_excludes_docs_path(self, client, caplog_fixture):
        """Test that /docs path is excluded from logging."""
        response = client.get("/docs")

        assert response.status_code == 200

        # Check that /docs is NOT in middleware logs
        middleware_records = [r for r in caplog_fixture.records if r.name == "app.middleware.logging_middleware"]
        log_messages = [record.message for record in middleware_records]
        assert not any("/docs" in msg for msg in log_messages)

    def test_includes_duration_in_logs(self, client, caplog_fixture):
        """Test that request duration is logged."""
        response = client.get("/test")

        assert response.status_code == 200

        # Check that duration_ms is in log records
        duration_found = False
        for record in caplog_fixture.records:
            if hasattr(record, 'duration_ms'):
                assert isinstance(record.duration_ms, (int, float))
                assert record.duration_ms >= 0
                duration_found = True
                break

        assert duration_found, "Duration not found in logs"

    def test_includes_request_details(self, client, caplog_fixture):
        """Test that request details (method, path) are logged."""
        response = client.get("/test")

        assert response.status_code == 200

        # Check request details in log records
        for record in caplog_fixture.records:
            if hasattr(record, 'method'):
                assert record.method == "GET"
                assert record.path == "/test"
                assert hasattr(record, 'request_id')
                break
        else:
            pytest.fail("Request details not found in logs")

    def test_includes_status_code_in_logs(self, client, caplog_fixture):
        """Test that response status code is logged."""
        response = client.get("/test")

        assert response.status_code == 200

        # Check status code in log records
        status_found = False
        for record in caplog_fixture.records:
            if hasattr(record, 'status_code'):
                assert record.status_code == 200
                status_found = True
                break

        assert status_found, "Status code not found in logs"

    def test_different_http_methods(self, client, caplog_fixture):
        """Test logging works for different HTTP methods."""
        # Test POST
        response = client.post("/test-post", json={"key": "value"})
        assert response.status_code == 200

        log_messages = [record.message for record in caplog_fixture.records]
        assert any("POST /test-post" in msg for msg in log_messages)

    def test_request_id_is_unique(self, client):
        """Test that each request gets a unique request ID."""
        response1 = client.get("/test")
        response2 = client.get("/test")

        request_id1 = response1.headers["X-Request-ID"]
        request_id2 = response2.headers["X-Request-ID"]

        assert request_id1 != request_id2

    def test_logs_client_ip(self, client, caplog_fixture):
        """Test that client IP is logged."""
        response = client.get("/test")

        assert response.status_code == 200

        # Check client IP in log records
        ip_found = False
        for record in caplog_fixture.records:
            if hasattr(record, 'client_ip'):
                assert record.client_ip is not None
                ip_found = True
                break

        assert ip_found, "Client IP not found in logs"


class TestSensitiveDataRedaction:
    """Tests for sensitive data redaction."""

    def test_redact_password(self):
        """Test that password fields are redacted."""
        middleware = RequestLoggingMiddleware(app=None)

        data = {
            "username": "test",
            "password": "secret123"
        }

        redacted = middleware._redact_sensitive_data(data)

        assert redacted["username"] == "test"
        assert redacted["password"] == "***REDACTED***"

    def test_redact_multiple_sensitive_fields(self):
        """Test that multiple sensitive fields are redacted."""
        middleware = RequestLoggingMiddleware(app=None)

        data = {
            "email": "test@example.com",
            "password": "secret123",
            "current_password": "old_secret",
            "new_password": "new_secret",
            "token": "jwt_token",
            "access_token": "access",
            "secret": "secret_value"
        }

        redacted = middleware._redact_sensitive_data(data)

        assert redacted["email"] == "test@example.com"
        assert redacted["password"] == "***REDACTED***"
        assert redacted["current_password"] == "***REDACTED***"
        assert redacted["new_password"] == "***REDACTED***"
        assert redacted["token"] == "***REDACTED***"
        assert redacted["access_token"] == "***REDACTED***"
        assert redacted["secret"] == "***REDACTED***"

    def test_redact_nested_sensitive_data(self):
        """Test that nested sensitive fields are redacted."""
        middleware = RequestLoggingMiddleware(app=None)

        data = {
            "user": {
                "name": "Test",
                "password": "secret"
            },
            "credentials": {
                "token": "jwt_token",
                "email": "test@example.com"
            }
        }

        redacted = middleware._redact_sensitive_data(data)

        assert redacted["user"]["name"] == "Test"
        assert redacted["user"]["password"] == "***REDACTED***"
        assert redacted["credentials"]["token"] == "***REDACTED***"
        assert redacted["credentials"]["email"] == "test@example.com"

    def test_redact_case_insensitive(self):
        """Test that redaction is case-insensitive."""
        middleware = RequestLoggingMiddleware(app=None)

        data = {
            "Password": "secret",
            "PASSWORD": "secret",
            "AccessToken": "token"
        }

        redacted = middleware._redact_sensitive_data(data)

        assert redacted["Password"] == "***REDACTED***"
        assert redacted["PASSWORD"] == "***REDACTED***"
        assert redacted["AccessToken"] == "***REDACTED***"

    def test_non_dict_data_returns_unchanged(self):
        """Test that non-dict data is returned unchanged."""
        middleware = RequestLoggingMiddleware(app=None)

        assert middleware._redact_sensitive_data("string") == "string"
        assert middleware._redact_sensitive_data(123) == 123
        assert middleware._redact_sensitive_data(None) is None
