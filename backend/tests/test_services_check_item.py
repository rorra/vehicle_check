import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.check_item_service import CheckItemService
from app.models import CheckItemTemplate, ItemCheck, InspectionResult, generate_uuid


class TestCheckItemServiceList:
    """Test the list service method."""

    def test_list_returns_all_templates_ordered(self, db_session: Session):
        """List returns all templates ordered by ordinal."""
        service = CheckItemService(db_session)

        # Create templates with different ordinals
        template1 = CheckItemTemplate(id=generate_uuid(), code="CODE1", description="First", ordinal=2)
        template2 = CheckItemTemplate(id=generate_uuid(), code="CODE2", description="Second", ordinal=1)
        template3 = CheckItemTemplate(id=generate_uuid(), code="CODE3", description="Third", ordinal=3)

        db_session.add_all([template1, template2, template3])
        db_session.commit()

        result = service.list()

        assert len(result) == 3
        assert result[0].ordinal == 1
        assert result[1].ordinal == 2
        assert result[2].ordinal == 3


class TestCheckItemServiceGet:
    """Test the get service method."""

    def test_get_returns_template(self, db_session: Session):
        """Get returns the template by ID."""
        template = CheckItemTemplate(id=generate_uuid(), code="TEST", description="Test", ordinal=1)
        db_session.add(template)
        db_session.commit()

        service = CheckItemService(db_session)
        result = service.get(template.id)

        assert result.id == template.id
        assert result.code == "TEST"

    def test_get_nonexistent_raises_404(self, db_session: Session):
        """Get with nonexistent ID raises 404."""
        service = CheckItemService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.get(generate_uuid())

        assert exc_info.value.status_code == 404


class TestCheckItemServiceCreate:
    """Test the create service method."""

    def test_create_with_valid_data(self, db_session: Session):
        """Create template with valid data."""
        service = CheckItemService(db_session)
        result = service.create("BRAKES", "Brake system check", 1)

        assert result.code == "BRAKES"
        assert result.description == "Brake system check"
        assert result.ordinal == 1

    def test_create_uppercases_code(self, db_session: Session):
        """Create automatically uppercases the code."""
        service = CheckItemService(db_session)
        result = service.create("brakes", "Brake system check", 1)

        assert result.code == "BRAKES"

    def test_create_with_duplicate_code_fails(self, db_session: Session):
        """Cannot create template with duplicate code."""
        template = CheckItemTemplate(id=generate_uuid(), code="DUPLICATE", description="Test", ordinal=1)
        db_session.add(template)
        db_session.commit()

        service = CheckItemService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.create("duplicate", "Another", 2)

        assert exc_info.value.status_code == 400
        assert "código" in exc_info.value.detail.lower()

    def test_create_with_duplicate_ordinal_fails(self, db_session: Session):
        """Cannot create template with duplicate ordinal."""
        template = CheckItemTemplate(id=generate_uuid(), code="FIRST", description="Test", ordinal=1)
        db_session.add(template)
        db_session.commit()

        service = CheckItemService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.create("SECOND", "Another", 1)

        assert exc_info.value.status_code == 400
        assert "orden" in exc_info.value.detail.lower()


class TestCheckItemServiceUpdate:
    """Test the update service method."""

    def test_update_code(self, db_session: Session):
        """Can update template code."""
        template = CheckItemTemplate(id=generate_uuid(), code="OLD", description="Test", ordinal=1)
        db_session.add(template)
        db_session.commit()

        service = CheckItemService(db_session)
        result = service.update(template.id, code="new")

        assert result.code == "NEW"

    def test_update_description(self, db_session: Session):
        """Can update template description."""
        template = CheckItemTemplate(id=generate_uuid(), code="TEST", description="Old", ordinal=1)
        db_session.add(template)
        db_session.commit()

        service = CheckItemService(db_session)
        result = service.update(template.id, description="New description")

        assert result.description == "New description"

    def test_update_ordinal(self, db_session: Session):
        """Can update template ordinal."""
        template = CheckItemTemplate(id=generate_uuid(), code="TEST", description="Test", ordinal=1)
        db_session.add(template)
        db_session.commit()

        service = CheckItemService(db_session)
        result = service.update(template.id, ordinal=5)

        assert result.ordinal == 5

    def test_update_nonexistent_raises_404(self, db_session: Session):
        """Update nonexistent template raises 404."""
        service = CheckItemService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.update(generate_uuid(), code="NEW")

        assert exc_info.value.status_code == 404

    def test_update_to_duplicate_code_fails(self, db_session: Session):
        """Cannot update to duplicate code."""
        template1 = CheckItemTemplate(id=generate_uuid(), code="FIRST", description="Test", ordinal=1)
        template2 = CheckItemTemplate(id=generate_uuid(), code="SECOND", description="Test", ordinal=2)
        db_session.add_all([template1, template2])
        db_session.commit()

        service = CheckItemService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.update(template2.id, code="FIRST")

        assert exc_info.value.status_code == 400

    def test_update_to_duplicate_ordinal_fails(self, db_session: Session):
        """Cannot update to duplicate ordinal."""
        template1 = CheckItemTemplate(id=generate_uuid(), code="FIRST", description="Test", ordinal=1)
        template2 = CheckItemTemplate(id=generate_uuid(), code="SECOND", description="Test", ordinal=2)
        db_session.add_all([template1, template2])
        db_session.commit()

        service = CheckItemService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.update(template2.id, ordinal=1)

        assert exc_info.value.status_code == 400


class TestCheckItemServiceDelete:
    """Test the delete service method."""

    def test_delete_unused_template(self, db_session: Session):
        """Can delete template that is not being used."""
        template = CheckItemTemplate(id=generate_uuid(), code="TEST", description="Test", ordinal=1)
        db_session.add(template)
        db_session.commit()

        service = CheckItemService(db_session)
        service.delete(template.id)

        # Verify it was deleted
        assert db_session.query(CheckItemTemplate).filter(CheckItemTemplate.id == template.id).first() is None

    def test_delete_nonexistent_raises_404(self, db_session: Session):
        """Delete nonexistent template raises 404."""
        service = CheckItemService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.delete(generate_uuid())

        assert exc_info.value.status_code == 404

    def test_cannot_delete_template_in_use(self, db_session: Session):
        """Cannot delete template that is being used in inspections."""
        from app.models import Vehicle, User, UserRole, AnnualInspection, Appointment
        from app.schemas.auth import UserRegister
        from app.services.auth_service import AuthService
        from datetime import datetime, timezone, timedelta

        # Create necessary entities
        auth_service = AuthService(db_session)
        user = auth_service.register_user(UserRegister(
            name="Test User",
            email="test@test.com",
            password="Password123",
            role=UserRole.CLIENT
        ))

        vehicle = Vehicle(
            id=generate_uuid(),
            plate_number="ABC123",
            make="Toyota",
            model="Corolla",
            year=2020,
            owner_id=user.id
        )
        db_session.add(vehicle)

        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=vehicle.id,
            year=2024,
            status="PENDING",
            attempt_count=0
        )
        db_session.add(annual)

        appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=annual.id,
            vehicle_id=vehicle.id,
            created_by_user_id=user.id,
            created_channel="CLIENT_PORTAL",
            date_time=datetime.now(timezone.utc) + timedelta(days=1),
            status="CONFIRMED",
            confirmation_token="TEST123"
        )
        db_session.add(appointment)
        db_session.commit()

        # Create template
        template = CheckItemTemplate(id=generate_uuid(), code="TEST", description="Test", ordinal=1)
        db_session.add(template)
        db_session.commit()

        # Create an inspection result using this template
        result_id = generate_uuid()
        inspection_result = InspectionResult(
            id=result_id,
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=50
        )
        item_check = ItemCheck(
            id=generate_uuid(),
            inspection_result_id=result_id,
            check_item_template_id=template.id,
            score=10
        )
        db_session.add_all([inspection_result, item_check])
        db_session.commit()

        service = CheckItemService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.delete(template.id)

        assert exc_info.value.status_code == 400
        assert "siendo usada" in exc_info.value.detail
