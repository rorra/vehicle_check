import pytest
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.services.appointment_service import AppointmentService
from app.models import (
    User,
    UserRole,
    Inspector,
    Vehicle,
    AnnualInspection,
    Appointment,
    AppointmentStatus,
    AnnualStatus,
    CreatedChannel,
    CheckItemTemplate,
    InspectionResult,
    ItemCheck,
    generate_uuid,
)
from app.schemas.appointment import CompleteAppointmentRequest


class TestAppointmentServiceCompleteWithInspection:
    """Test the complete_with_inspection service method."""

    @pytest.fixture
    def inspector_user(self, db_session: Session) -> User:
        """Create an inspector user."""
        user = User(
            id=generate_uuid(),
            name="Test Inspector",
            email=f"inspector-{generate_uuid()}@example.com",
            role=UserRole.INSPECTOR,
            password_hash="hashed_password",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()
        return user

    @pytest.fixture
    def inspector(self, db_session: Session, inspector_user: User) -> Inspector:
        """Create an inspector profile."""
        inspector = Inspector(
            id=generate_uuid(),
            user_id=inspector_user.id,
            employee_id=f"INS-{generate_uuid()[:8]}",
            active=True,
        )
        db_session.add(inspector)
        db_session.commit()
        return inspector

    @pytest.fixture
    def vehicle(self, db_session: Session, sample_user: User) -> Vehicle:
        """Create a test vehicle."""
        vehicle = Vehicle(
            id=generate_uuid(),
            plate_number=f"TEST-{generate_uuid()[:8]}",
            owner_id=sample_user.id,
            make="Toyota",
            model="Corolla",
            year=2020,
        )
        db_session.add(vehicle)
        db_session.commit()
        return vehicle

    @pytest.fixture
    def annual_inspection(self, db_session: Session, vehicle: Vehicle) -> AnnualInspection:
        """Create an annual inspection."""
        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()
        return annual

    @pytest.fixture
    def confirmed_appointment(
        self,
        db_session: Session,
        annual_inspection: AnnualInspection,
        inspector: Inspector,
        vehicle: Vehicle,
        sample_user: User
    ) -> Appointment:
        """Create a confirmed appointment."""
        appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=annual_inspection.id,
            vehicle_id=vehicle.id,
            inspector_id=inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=datetime.now(timezone.utc) + timedelta(days=1),
            status=AppointmentStatus.CONFIRMED,
            confirmation_token=f"CONF-{generate_uuid()[:8]}",
        )
        db_session.add(appointment)
        db_session.commit()
        return appointment

    @pytest.fixture
    def check_templates(self, db_session: Session):
        """Create the 8 standard check item templates."""
        templates_data = [
            ("BRK", "Frenos"),
            ("LGT", "Luces e indicadores"),
            ("TIR", "Neumáticos"),
            ("ENG", "Motor y fugas"),
            ("STE", "Dirección"),
            ("SUS", "Suspensión"),
            ("EMI", "Emisiones"),
            ("SAF", "Elementos de seguridad"),
        ]

        templates = []
        for idx, (code, desc) in enumerate(templates_data, start=1):
            template = CheckItemTemplate(
                id=generate_uuid(),
                code=code,
                description=desc,
                ordinal=idx,
            )
            db_session.add(template)
            templates.append(template)

        db_session.commit()
        return templates

    def test_successful_completion_with_passing_score(
        self,
        db_session: Session,
        inspector_user: User,
        inspector: Inspector,
        confirmed_appointment: Appointment,
        check_templates
    ):
        """Successfully complete an appointment with a passing score."""
        # Arrange
        service = AppointmentService(db_session)
        result_data = CompleteAppointmentRequest(
            total_score=45,
            item_scores=[6, 6, 6, 6, 6, 5, 5, 5],
            owner_observation="Todo en buen estado"
        )

        # Act
        result = service.complete_with_inspection(
            confirmed_appointment.id,
            result_data,
            inspector_user
        )

        # Assert
        assert result.status == AppointmentStatus.COMPLETED

        # Verify inspection result was created
        inspection_result = db_session.query(InspectionResult).filter(
            InspectionResult.appointment_id == confirmed_appointment.id
        ).first()
        assert inspection_result is not None
        assert inspection_result.total_score == 45
        assert inspection_result.owner_observation == "Todo en buen estado"

        # Verify item checks were created
        item_checks = db_session.query(ItemCheck).filter(
            ItemCheck.inspection_result_id == inspection_result.id
        ).all()
        assert len(item_checks) == 8

        # Verify annual inspection was updated
        annual = db_session.query(AnnualInspection).filter(
            AnnualInspection.id == confirmed_appointment.annual_inspection_id
        ).first()
        assert annual.status == AnnualStatus.PASSED
        assert annual.current_result_id == inspection_result.id
        assert annual.attempt_count == 1

    def test_successful_completion_with_failing_score(
        self,
        db_session: Session,
        inspector_user: User,
        inspector: Inspector,
        confirmed_appointment: Appointment,
        check_templates
    ):
        """Successfully complete an appointment with a failing score."""
        # Arrange
        service = AppointmentService(db_session)
        result_data = CompleteAppointmentRequest(
            total_score=35,
            item_scores=[5, 5, 4, 4, 4, 4, 5, 4],
            owner_observation="Requiere reparaciones"
        )

        # Act
        result = service.complete_with_inspection(
            confirmed_appointment.id,
            result_data,
            inspector_user
        )

        # Assert
        assert result.status == AppointmentStatus.COMPLETED

        # Verify annual inspection is marked as failed
        annual = db_session.query(AnnualInspection).filter(
            AnnualInspection.id == confirmed_appointment.annual_inspection_id
        ).first()
        assert annual.status == AnnualStatus.FAILED
        assert annual.attempt_count == 1

    def test_inspector_not_found(
        self,
        db_session: Session,
        sample_user: User,
        confirmed_appointment: Appointment,
        check_templates
    ):
        """Raise error when user is not an inspector."""
        # Arrange
        service = AppointmentService(db_session)
        result_data = CompleteAppointmentRequest(
            total_score=45,
            item_scores=[6, 6, 6, 6, 6, 5, 5, 5],
            owner_observation="Test"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.complete_with_inspection(
                confirmed_appointment.id,
                result_data,
                sample_user  # This is a CLIENT, not an INSPECTOR
            )

        assert exc_info.value.status_code == 404
        assert "Inspector no encontrado" in exc_info.value.detail

    def test_appointment_not_found(
        self,
        db_session: Session,
        inspector_user: User,
        inspector: Inspector,
        check_templates
    ):
        """Raise error when appointment doesn't exist."""
        # Arrange
        service = AppointmentService(db_session)
        result_data = CompleteAppointmentRequest(
            total_score=45,
            item_scores=[6, 6, 6, 6, 6, 5, 5, 5],
            owner_observation="Test"
        )
        fake_appointment_id = generate_uuid()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.complete_with_inspection(
                fake_appointment_id,
                result_data,
                inspector_user
            )

        assert exc_info.value.status_code == 404
        assert "Turno no encontrado" in exc_info.value.detail

    def test_inspector_not_assigned_to_appointment(
        self,
        db_session: Session,
        confirmed_appointment: Appointment,
        check_templates
    ):
        """Raise error when inspector is not assigned to the appointment."""
        # Arrange - Create a different inspector
        other_inspector_user = User(
            id=generate_uuid(),
            name="Other Inspector",
            email=f"other-inspector-{generate_uuid()}@example.com",
            role=UserRole.INSPECTOR,
            password_hash="hashed_password",
            is_active=True,
        )
        db_session.add(other_inspector_user)
        db_session.commit()

        other_inspector = Inspector(
            id=generate_uuid(),
            user_id=other_inspector_user.id,
            employee_id=f"INS-{generate_uuid()[:8]}",
            active=True,
        )
        db_session.add(other_inspector)
        db_session.commit()

        service = AppointmentService(db_session)
        result_data = CompleteAppointmentRequest(
            total_score=45,
            item_scores=[6, 6, 6, 6, 6, 5, 5, 5],
            owner_observation="Test"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.complete_with_inspection(
                confirmed_appointment.id,
                result_data,
                other_inspector_user
            )

        assert exc_info.value.status_code == 403
        assert "Este turno no está asignado a ti" in exc_info.value.detail

    def test_appointment_not_confirmed(
        self,
        db_session: Session,
        inspector_user: User,
        inspector: Inspector,
        annual_inspection: AnnualInspection,
        vehicle: Vehicle,
        sample_user: User,
        check_templates
    ):
        """Raise error when appointment is not confirmed."""
        # Arrange - Create a pending appointment
        pending_appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=annual_inspection.id,
            vehicle_id=vehicle.id,
            inspector_id=inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=datetime.now(timezone.utc) + timedelta(days=1),
            status=AppointmentStatus.PENDING,
            confirmation_token=f"CONF-{generate_uuid()[:8]}",
        )
        db_session.add(pending_appointment)
        db_session.commit()

        service = AppointmentService(db_session)
        result_data = CompleteAppointmentRequest(
            total_score=45,
            item_scores=[6, 6, 6, 6, 6, 5, 5, 5],
            owner_observation="Test"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.complete_with_inspection(
                pending_appointment.id,
                result_data,
                inspector_user
            )

        assert exc_info.value.status_code == 400
        assert "Solo se pueden completar turnos confirmados" in exc_info.value.detail

    def test_templates_not_configured(
        self,
        db_session: Session,
        inspector_user: User,
        inspector: Inspector,
        confirmed_appointment: Appointment
    ):
        """Raise error when check item templates are not properly configured."""
        # Arrange - Don't create templates (or create wrong number)
        # Only create 5 templates instead of 8
        for i in range(5):
            template = CheckItemTemplate(
                id=generate_uuid(),
                code=f"TST{i}",
                description=f"Test {i}",
                ordinal=i + 1,
            )
            db_session.add(template)
        db_session.commit()

        service = AppointmentService(db_session)
        result_data = CompleteAppointmentRequest(
            total_score=45,
            item_scores=[6, 6, 6, 6, 6, 5, 5, 5],
            owner_observation="Test"
        )

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            service.complete_with_inspection(
                confirmed_appointment.id,
                result_data,
                inspector_user
            )

        assert exc_info.value.status_code == 500
        assert "Plantillas de chequeo no configuradas correctamente" in exc_info.value.detail

    def test_item_checks_have_correct_observations(
        self,
        db_session: Session,
        inspector_user: User,
        inspector: Inspector,
        confirmed_appointment: Appointment,
        check_templates
    ):
        """Verify that item checks have correct observations based on score."""
        # Arrange
        service = AppointmentService(db_session)
        # Mix of passing (>=5) and failing (<5) scores
        result_data = CompleteAppointmentRequest(
            total_score=40,
            item_scores=[6, 4, 7, 3, 5, 8, 2, 5],
            owner_observation="Mixed results"
        )

        # Act
        service.complete_with_inspection(
            confirmed_appointment.id,
            result_data,
            inspector_user
        )

        # Assert
        inspection_result = db_session.query(InspectionResult).filter(
            InspectionResult.appointment_id == confirmed_appointment.id
        ).first()

        # Get item checks ordered by template ordinal
        item_checks = db_session.query(ItemCheck).join(
            CheckItemTemplate, ItemCheck.check_item_template_id == CheckItemTemplate.id
        ).filter(
            ItemCheck.inspection_result_id == inspection_result.id
        ).order_by(CheckItemTemplate.ordinal).all()

        # Check observations match scores
        for item_check, score in zip(item_checks, result_data.item_scores):
            if score >= 5:
                assert item_check.observation == "Chequeo realizado"
            else:
                assert item_check.observation == "Requiere atención"


class TestAppointmentServiceCreate:
    """Test the create service method."""

    def test_client_can_create_for_own_vehicle(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle
    ):
        """Client can create appointment for their own vehicle."""
        from app.schemas.appointment import AppointmentCreate

        # Create annual inspection
        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()

        service = AppointmentService(db_session)
        data = AppointmentCreate(
            vehicle_id=client_vehicle.id,
            annual_inspection_id=annual.id,
            date_time=datetime.now(timezone.utc) + timedelta(days=1)
        )

        result = service.create(data, client_user)

        assert result.vehicle_id == client_vehicle.id
        assert result.annual_inspection_id == annual.id
        assert result.status == AppointmentStatus.CONFIRMED
        assert result.created_channel == CreatedChannel.CLIENT_PORTAL

    def test_auto_create_annual_inspection_when_not_provided(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle
    ):
        """Appointment creation auto-creates annual inspection if not provided."""
        from app.schemas.appointment import AppointmentCreate

        service = AppointmentService(db_session)
        data = AppointmentCreate(
            vehicle_id=client_vehicle.id,
            annual_inspection_id=None,  # Not provided
            date_time=datetime.now(timezone.utc) + timedelta(days=1)
        )

        result = service.create(data, client_user)

        # Verify annual inspection was auto-created
        annual = db_session.query(AnnualInspection).filter(
            AnnualInspection.vehicle_id == client_vehicle.id,
            AnnualInspection.year == datetime.now().year
        ).first()

        assert annual is not None
        assert result.annual_inspection_id == annual.id
        assert annual.status == AnnualStatus.PENDING

    def test_rejects_appointment_if_current_year_already_passed(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle
    ):
        """Cannot create appointment if current year inspection already passed."""
        from app.schemas.appointment import AppointmentCreate

        # Create PASSED annual inspection for current year
        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PASSED,
            attempt_count=1,
        )
        db_session.add(annual)
        db_session.commit()

        service = AppointmentService(db_session)
        data = AppointmentCreate(
            vehicle_id=client_vehicle.id,
            annual_inspection_id=None,
            date_time=datetime.now(timezone.utc) + timedelta(days=1)
        )

        with pytest.raises(HTTPException) as exc_info:
            service.create(data, client_user)

        assert exc_info.value.status_code == 400
        assert "ya fue aprobada" in exc_info.value.detail

    def test_uses_existing_annual_inspection_if_not_passed(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle
    ):
        """Uses existing annual inspection if current year exists but not passed."""
        from app.schemas.appointment import AppointmentCreate

        # Create PENDING annual inspection for current year
        existing_annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(existing_annual)
        db_session.commit()

        service = AppointmentService(db_session)
        data = AppointmentCreate(
            vehicle_id=client_vehicle.id,
            annual_inspection_id=None,
            date_time=datetime.now(timezone.utc) + timedelta(days=1)
        )

        result = service.create(data, client_user)

        # Should use existing annual inspection, not create new one
        assert result.annual_inspection_id == existing_annual.id

        # Verify no duplicate was created
        annual_count = db_session.query(AnnualInspection).filter(
            AnnualInspection.vehicle_id == client_vehicle.id,
            AnnualInspection.year == datetime.now().year
        ).count()
        assert annual_count == 1

    def test_inspector_cannot_create(
        self,
        db_session: Session,
        inspector_user: User,
        client_vehicle: Vehicle
    ):
        """Inspector cannot create appointments."""
        from app.schemas.appointment import AppointmentCreate

        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()

        service = AppointmentService(db_session)
        data = AppointmentCreate(
            vehicle_id=client_vehicle.id,
            annual_inspection_id=annual.id,
            date_time=datetime.now(timezone.utc) + timedelta(days=1)
        )

        with pytest.raises(HTTPException) as exc_info:
            service.create(data, inspector_user)

        assert exc_info.value.status_code == 403

    def test_client_cannot_create_for_other_vehicle(
        self,
        db_session: Session,
        client_user: User,
        sample_user: User
    ):
        """Client cannot create appointment for other user's vehicle."""
        from app.schemas.appointment import AppointmentCreate

        # Create vehicle for another user
        other_vehicle = Vehicle(
            id=generate_uuid(),
            plate_number=f"OTHER-{generate_uuid()[:8]}",
            owner_id=sample_user.id,
            make="Honda",
            model="Civic",
            year=2021,
        )
        db_session.add(other_vehicle)
        db_session.commit()

        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=other_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()

        service = AppointmentService(db_session)
        data = AppointmentCreate(
            vehicle_id=other_vehicle.id,
            annual_inspection_id=annual.id,
            date_time=datetime.now(timezone.utc) + timedelta(days=1)
        )

        with pytest.raises(HTTPException) as exc_info:
            service.create(data, client_user)

        assert exc_info.value.status_code == 403


class TestAppointmentServiceList:
    """Test the list service method."""

    def test_client_sees_only_own_appointments(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle,
        sample_user: User,
        sample_inspector: Inspector
    ):
        """Client can only see appointments for their own vehicles."""
        # Create appointment for client
        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()

        client_appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=annual.id,
            vehicle_id=client_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=client_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=datetime.now(timezone.utc) + timedelta(days=1),
            status=AppointmentStatus.CONFIRMED,
            confirmation_token=f"CONF-{generate_uuid()[:8]}",
        )
        db_session.add(client_appointment)

        # Create vehicle and appointment for another user
        other_vehicle = Vehicle(
            id=generate_uuid(),
            plate_number=f"OTHER-{generate_uuid()[:8]}",
            owner_id=sample_user.id,
            make="Honda",
            model="Civic",
            year=2021,
        )
        db_session.add(other_vehicle)
        db_session.commit()

        other_annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=other_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(other_annual)
        db_session.commit()

        other_appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=other_annual.id,
            vehicle_id=other_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=datetime.now(timezone.utc) + timedelta(days=2),
            status=AppointmentStatus.CONFIRMED,
            confirmation_token=f"CONF-{generate_uuid()[:8]}",
        )
        db_session.add(other_appointment)
        db_session.commit()

        service = AppointmentService(db_session)
        appointments, total = service.list(client_user)

        assert total == 1
        assert len(appointments) == 1
        assert appointments[0].id == client_appointment.id

    def test_inspector_sees_only_assigned_appointments(
        self,
        db_session: Session,
        inspector_user: User,
        sample_inspector: Inspector,
        client_vehicle: Vehicle,
        client_user: User
    ):
        """Inspector can only see their assigned appointments."""
        # Create inspector for inspector_user
        inspector = Inspector(
            id=generate_uuid(),
            user_id=inspector_user.id,
            employee_id=f"INS-{generate_uuid()[:8]}",
            active=True,
        )
        db_session.add(inspector)
        db_session.commit()

        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()

        # Create appointment assigned to inspector_user
        my_appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=annual.id,
            vehicle_id=client_vehicle.id,
            inspector_id=inspector.id,
            created_by_user_id=client_user.id,
            created_channel=CreatedChannel.ADMIN_PANEL,
            date_time=datetime.now(timezone.utc) + timedelta(days=1),
            status=AppointmentStatus.CONFIRMED,
            confirmation_token=f"CONF-{generate_uuid()[:8]}",
        )
        db_session.add(my_appointment)

        # Create appointment assigned to another inspector
        other_appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=annual.id,
            vehicle_id=client_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=client_user.id,
            created_channel=CreatedChannel.ADMIN_PANEL,
            date_time=datetime.now(timezone.utc) + timedelta(days=2),
            status=AppointmentStatus.CONFIRMED,
            confirmation_token=f"CONF-{generate_uuid()[:8]}",
        )
        db_session.add(other_appointment)
        db_session.commit()

        service = AppointmentService(db_session)
        appointments, total = service.list(inspector_user)

        assert total == 1
        assert len(appointments) == 1
        assert appointments[0].id == my_appointment.id


class TestAppointmentServiceGet:
    """Test the get service method."""

    def test_client_can_access_own_appointment(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle,
        sample_inspector: Inspector
    ):
        """Client can access appointment for their own vehicle."""
        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=annual.id,
            vehicle_id=client_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=client_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=datetime.now(timezone.utc) + timedelta(days=1),
            status=AppointmentStatus.CONFIRMED,
            confirmation_token=f"CONF-{generate_uuid()[:8]}",
        )
        db_session.add(appointment)
        db_session.commit()

        service = AppointmentService(db_session)
        result = service.get(appointment.id, client_user)

        assert result.id == appointment.id

    def test_client_cannot_access_other_appointment(
        self,
        db_session: Session,
        client_user: User,
        sample_user: User,
        sample_inspector: Inspector
    ):
        """Client cannot access appointment for other user's vehicle."""
        # Create vehicle for another user
        other_vehicle = Vehicle(
            id=generate_uuid(),
            plate_number=f"OTHER-{generate_uuid()[:8]}",
            owner_id=sample_user.id,
            make="Honda",
            model="Civic",
            year=2021,
        )
        db_session.add(other_vehicle)
        db_session.commit()

        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=other_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=annual.id,
            vehicle_id=other_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=sample_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=datetime.now(timezone.utc) + timedelta(days=1),
            status=AppointmentStatus.CONFIRMED,
            confirmation_token=f"CONF-{generate_uuid()[:8]}",
        )
        db_session.add(appointment)
        db_session.commit()

        service = AppointmentService(db_session)
        with pytest.raises(HTTPException) as exc_info:
            service.get(appointment.id, client_user)

        assert exc_info.value.status_code == 403


class TestAppointmentServiceUpdate:
    """Test the update service method."""

    def test_client_can_update_date(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle,
        sample_inspector: Inspector
    ):
        """Client can update appointment date."""
        from app.schemas.appointment import AppointmentUpdate

        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=annual.id,
            vehicle_id=client_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=client_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=datetime.now(timezone.utc) + timedelta(days=1),
            status=AppointmentStatus.CONFIRMED,
            confirmation_token=f"CONF-{generate_uuid()[:8]}",
        )
        db_session.add(appointment)
        db_session.commit()

        service = AppointmentService(db_session)
        new_date = datetime.now(timezone.utc) + timedelta(days=5)
        data = AppointmentUpdate(date_time=new_date)
        result = service.update(appointment.id, data, client_user)

        # Compare dates - allow for small timing differences (within 2 seconds)
        time_diff = abs((result.date_time - new_date.replace(tzinfo=None)).total_seconds())
        assert time_diff < 2

    def test_inspector_cannot_update(
        self,
        db_session: Session,
        inspector_user: User,
        client_vehicle: Vehicle,
        client_user: User,
        sample_inspector: Inspector
    ):
        """Inspector cannot update appointments."""
        from app.schemas.appointment import AppointmentUpdate

        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=annual.id,
            vehicle_id=client_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=client_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=datetime.now(timezone.utc) + timedelta(days=1),
            status=AppointmentStatus.CONFIRMED,
            confirmation_token=f"CONF-{generate_uuid()[:8]}",
        )
        db_session.add(appointment)
        db_session.commit()

        service = AppointmentService(db_session)
        data = AppointmentUpdate(date_time=datetime.now(timezone.utc) + timedelta(days=5))

        with pytest.raises(HTTPException) as exc_info:
            service.update(appointment.id, data, inspector_user)

        assert exc_info.value.status_code == 403


class TestAppointmentServiceCancel:
    """Test the cancel service method."""

    def test_client_can_cancel_own_appointment(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle,
        sample_inspector: Inspector
    ):
        """Client can cancel their own appointment."""
        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=annual.id,
            vehicle_id=client_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=client_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=datetime.now(timezone.utc) + timedelta(days=1),
            status=AppointmentStatus.CONFIRMED,
            confirmation_token=f"CONF-{generate_uuid()[:8]}",
        )
        db_session.add(appointment)
        db_session.commit()

        service = AppointmentService(db_session)
        service.cancel(appointment.id, client_user)

        # Verify cancelled
        cancelled = db_session.query(Appointment).filter(
            Appointment.id == appointment.id
        ).first()
        assert cancelled.status == AppointmentStatus.CANCELLED

    def test_client_cannot_cancel_completed_appointment(
        self,
        db_session: Session,
        client_user: User,
        client_vehicle: Vehicle,
        sample_inspector: Inspector
    ):
        """Client cannot cancel completed appointment."""
        annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=client_vehicle.id,
            year=datetime.now().year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        db_session.add(annual)
        db_session.commit()

        appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=annual.id,
            vehicle_id=client_vehicle.id,
            inspector_id=sample_inspector.id,
            created_by_user_id=client_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL,
            date_time=datetime.now(timezone.utc) + timedelta(days=1),
            status=AppointmentStatus.COMPLETED,
            confirmation_token=f"CONF-{generate_uuid()[:8]}",
        )
        db_session.add(appointment)
        db_session.commit()

        service = AppointmentService(db_session)
        with pytest.raises(HTTPException) as exc_info:
            service.cancel(appointment.id, client_user)

        assert exc_info.value.status_code == 400


class TestAppointmentServiceGetAvailableSlots:
    """Test the get_available_slots service method."""

    def test_returns_only_future_unbooked_slots(
        self,
        db_session: Session
    ):
        """Returns only future unbooked slots."""
        from app.models import AvailabilitySlot

        # Create future unbooked slot (should be returned)
        future_slot = AvailabilitySlot(
            id=generate_uuid(),
            start_time=datetime.now(timezone.utc) + timedelta(days=1),
            end_time=datetime.now(timezone.utc) + timedelta(days=1, hours=1),
            is_booked=False,
        )
        db_session.add(future_slot)

        # Create past slot (should NOT be returned)
        past_slot = AvailabilitySlot(
            id=generate_uuid(),
            start_time=datetime.now(timezone.utc) - timedelta(days=1),
            end_time=datetime.now(timezone.utc) - timedelta(days=1, hours=-1),
            is_booked=False,
        )
        db_session.add(past_slot)

        # Create booked slot (should NOT be returned)
        booked_slot = AvailabilitySlot(
            id=generate_uuid(),
            start_time=datetime.now(timezone.utc) + timedelta(days=2),
            end_time=datetime.now(timezone.utc) + timedelta(days=2, hours=1),
            is_booked=True,
        )
        db_session.add(booked_slot)
        db_session.commit()

        service = AppointmentService(db_session)
        slots = service.get_available_slots()

        assert len(slots) == 1
        assert slots[0].id == future_slot.id
