from tests.conftest import utc_now
import pytest
from datetime import datetime
from app.models import (
    CheckItemTemplate,
    ItemCheck,
    InspectionResult,
    Appointment,
    AppointmentStatus,
    AnnualInspection,
    AnnualStatus,
    CreatedChannel,
)


class TestCheckItemTemplateModel:
    def test_create_check_item_template(self, db_session):
        """Test creating a check item template."""
        template = CheckItemTemplate(
            id="template-1",
            code="BRK",
            description="Frenos",
            ordinal=1,
        )
        db_session.add(template)
        db_session.commit()

        retrieved = db_session.query(CheckItemTemplate).filter_by(id="template-1").first()
        assert retrieved is not None
        assert retrieved.code == "BRK"
        assert retrieved.description == "Frenos"
        assert retrieved.ordinal == 1

    def test_check_item_template_unique_code(self, db_session):
        """Test that template codes must be unique."""
        template1 = CheckItemTemplate(
            id="template-1",
            code="BRK",
            description="Frenos",
            ordinal=1,
        )
        template2 = CheckItemTemplate(
            id="template-2",
            code="BRK",
            description="Duplicate",
            ordinal=2,
        )

        db_session.add(template1)
        db_session.commit()

        db_session.add(template2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_check_item_template_unique_ordinal(self, db_session):
        """Test that template ordinals must be unique."""
        template1 = CheckItemTemplate(
            id="template-1",
            code="BRK",
            description="Frenos",
            ordinal=1,
        )
        template2 = CheckItemTemplate(
            id="template-2",
            code="LGT",
            description="Luces",
            ordinal=1,
        )

        db_session.add(template1)
        db_session.commit()

        db_session.add(template2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_check_item_template_ordering(self, db_session, sample_check_templates):
        """Test that templates can be ordered by ordinal."""
        templates = (
            db_session.query(CheckItemTemplate)
            .order_by(CheckItemTemplate.ordinal)
            .all()
        )

        assert len(templates) == 8
        for idx, template in enumerate(templates, start=1):
            assert template.ordinal == idx

    def test_check_item_template_repr(self, db_session):
        """Test check item template string representation."""
        template = CheckItemTemplate(
            id="template-1",
            code="BRK",
            description="Frenos",
            ordinal=1,
        )
        db_session.add(template)
        db_session.commit()

        repr_str = repr(template)
        assert "CheckItemTemplate" in repr_str
        assert template.code in repr_str


class TestItemCheckModel:
    def test_create_item_check(
        self,
        db_session,
        sample_vehicle,
        sample_inspector,
        sample_user,
        sample_check_templates,
    ):
        """Test creating an item check."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.IN_PROGRESS,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.COMPLETED,
        )
        db_session.add(appointment)
        db_session.commit()

        result = InspectionResult(
            id="result-1",
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=60,
        )
        db_session.add(result)
        db_session.commit()

        item_check = ItemCheck(
            id="check-1",
            inspection_result_id=result.id,
            check_item_template_id=sample_check_templates[0].id,
            score=8,
            observation="Sin problemas detectados",
        )
        db_session.add(item_check)
        db_session.commit()

        retrieved = db_session.query(ItemCheck).filter_by(id="check-1").first()
        assert retrieved is not None
        assert retrieved.inspection_result_id == result.id
        assert retrieved.check_item_template_id == sample_check_templates[0].id
        assert retrieved.score == 8
        assert retrieved.observation == "Sin problemas detectados"

    def test_item_check_unique_per_result(
        self,
        db_session,
        sample_vehicle,
        sample_inspector,
        sample_user,
        sample_check_templates,
    ):
        """Test that each template can only be checked once per inspection result."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.IN_PROGRESS,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.COMPLETED,
        )
        db_session.add(appointment)
        db_session.commit()

        result = InspectionResult(
            id="result-1",
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=60,
        )
        db_session.add(result)
        db_session.commit()

        check1 = ItemCheck(
            id="check-1",
            inspection_result_id=result.id,
            check_item_template_id=sample_check_templates[0].id,
            score=8,
        )
        check2 = ItemCheck(
            id="check-2",
            inspection_result_id=result.id,
            check_item_template_id=sample_check_templates[0].id,
            score=7,
        )

        db_session.add(check1)
        db_session.commit()

        db_session.add(check2)
        with pytest.raises(Exception):
            db_session.commit()

    def test_item_check_score_range(
        self,
        db_session,
        sample_vehicle,
        sample_inspector,
        sample_user,
        sample_check_templates,
    ):
        """Test that item check scores are in valid range (1-10)."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.IN_PROGRESS,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.COMPLETED,
        )
        db_session.add(appointment)
        db_session.commit()

        result = InspectionResult(
            id="result-1",
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=60,
        )
        db_session.add(result)
        db_session.commit()

        # Valid score (1-10)
        valid_check = ItemCheck(
            id="check-1",
            inspection_result_id=result.id,
            check_item_template_id=sample_check_templates[0].id,
            score=5,
        )
        db_session.add(valid_check)
        db_session.commit()

        retrieved = db_session.query(ItemCheck).filter_by(id="check-1").first()
        assert retrieved.score == 5

    def test_item_check_optional_observation(
        self,
        db_session,
        sample_vehicle,
        sample_inspector,
        sample_user,
        sample_check_templates,
    ):
        """Test that observations are optional."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.IN_PROGRESS,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.COMPLETED,
        )
        db_session.add(appointment)
        db_session.commit()

        result = InspectionResult(
            id="result-1",
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=60,
        )
        db_session.add(result)
        db_session.commit()

        check = ItemCheck(
            id="check-1",
            inspection_result_id=result.id,
            check_item_template_id=sample_check_templates[0].id,
            score=8,
            observation=None,
        )
        db_session.add(check)
        db_session.commit()

        retrieved = db_session.query(ItemCheck).filter_by(id="check-1").first()
        assert retrieved.observation is None

    def test_item_check_cascade_delete(
        self,
        db_session,
        sample_vehicle,
        sample_inspector,
        sample_user,
        sample_check_templates,
    ):
        """Test that item checks are deleted when inspection result is deleted."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.IN_PROGRESS,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.COMPLETED,
        )
        db_session.add(appointment)
        db_session.commit()

        result = InspectionResult(
            id="result-1",
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=60,
        )
        db_session.add(result)
        db_session.commit()

        check = ItemCheck(
            id="check-1",
            inspection_result_id=result.id,
            check_item_template_id=sample_check_templates[0].id,
            score=8,
        )
        db_session.add(check)
        db_session.commit()

        db_session.delete(result)
        db_session.commit()

        assert db_session.query(ItemCheck).filter_by(id="check-1").first() is None

    def test_complete_inspection_with_8_checks(
        self,
        db_session,
        sample_vehicle,
        sample_inspector,
        sample_user,
        sample_check_templates,
    ):
        """Test creating a complete inspection with all 8 item checks."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.IN_PROGRESS,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.COMPLETED,
        )
        db_session.add(appointment)
        db_session.commit()

        scores = [8, 7, 9, 8, 7, 8, 9, 6]
        total_score = sum(scores)

        result = InspectionResult(
            id="result-1",
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=total_score,
        )
        db_session.add(result)
        db_session.commit()

        for idx, (template, score) in enumerate(zip(sample_check_templates, scores)):
            check = ItemCheck(
                id=f"check-{idx + 1}",
                inspection_result_id=result.id,
                check_item_template_id=template.id,
                score=score,
                observation=f"Revisión del ítem {idx + 1}",
            )
            db_session.add(check)

        db_session.commit()

        checks = db_session.query(ItemCheck).filter_by(inspection_result_id=result.id).all()
        assert len(checks) == 8
        assert sum(check.score for check in checks) == total_score

    def test_item_check_repr(
        self,
        db_session,
        sample_vehicle,
        sample_inspector,
        sample_user,
        sample_check_templates,
    ):
        """Test item check string representation."""
        annual = AnnualInspection(
            id="annual-1",
            vehicle_id=sample_vehicle.id,
            year=2024,
            status=AnnualStatus.IN_PROGRESS,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id="appointment-1",
            annual_inspection_id=annual.id,
            vehicle_id=sample_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=utc_now(),
            status=AppointmentStatus.COMPLETED,
        )
        db_session.add(appointment)
        db_session.commit()

        result = InspectionResult(
            id="result-1",
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=60,
        )
        db_session.add(result)
        db_session.commit()

        check = ItemCheck(
            id="check-1",
            inspection_result_id=result.id,
            check_item_template_id=sample_check_templates[0].id,
            score=8,
        )
        db_session.add(check)
        db_session.commit()

        repr_str = repr(check)
        assert "ItemCheck" in repr_str
        assert "8" in repr_str
