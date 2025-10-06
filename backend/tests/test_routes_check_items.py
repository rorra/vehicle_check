"""
Tests for check item template endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models import CheckItemTemplate, generate_uuid
from tests.factories import CheckItemTemplateFactory


class TestCheckItemTemplateRoutes:
    """Test check item template HTTP endpoints."""

    def test_unauthenticated_request_fails(self, client: TestClient):
        """Test that unauthenticated requests are rejected."""
        response = client.get("/api/v1/check-items/")
        assert response.status_code == 403

    def test_list_templates_ordered(
        self, client: TestClient, db_session: Session, client_token: str
    ):
        """Test listing templates returns them ordered by ordinal."""
        # Create templates
        for i in [3, 1, 2]:
            template = CheckItemTemplateFactory.build(
                code=f"TST{i}",
                description=f"Test Item {i}",
                ordinal=i,
            )
            db_session.add(template)
        db_session.commit()

        response = client.get(
            "/api/v1/check-items/",
            headers={"Authorization": f"Bearer {client_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        test_templates = [t for t in data if t["code"].startswith("TST")]
        ordinals = [t["ordinal"] for t in test_templates]
        assert ordinals == sorted(ordinals)

    def test_get_template_by_id(
        self, client: TestClient, db_session: Session, client_token: str
    ):
        """Test get template by ID."""
        template = CheckItemTemplateFactory.build(
            id="test-template",
            code="BRK",
            description="Frenos",
            ordinal=1,
        )
        db_session.add(template)
        db_session.commit()

        response = client.get(
            "/api/v1/check-items/test-template",
            headers={"Authorization": f"Bearer {client_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "BRK"
        assert data["description"] == "Frenos"

    def test_get_nonexistent_template_returns_404(
        self, client: TestClient, admin_token: str
    ):
        """Test that getting nonexistent template returns 404."""
        response = client.get(
            "/api/v1/check-items/nonexistent",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 404

