from typing import List, Optional, Tuple
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import (
    Appointment,
    AnnualInspection,
    Vehicle,
    User,
    UserRole,
    AppointmentStatus,
    AnnualStatus,
    CreatedChannel,
    Inspector,
    InspectionResult,
    CheckItemTemplate,
    ItemCheck,
    AvailabilitySlot,
    generate_uuid,
)
from app.schemas.appointment import (
    CompleteAppointmentRequest,
    AppointmentCreate,
    AppointmentUpdate,
)


class AppointmentService:
    """Service layer for appointment business logic."""

    def __init__(self, db: Session):
        self.db = db

    def complete_with_inspection(
        self,
        appointment_id: str,
        result_data: CompleteAppointmentRequest,
        current_user: User
    ) -> Appointment:
        """
        Complete an appointment and record inspection results.

        Args:
            appointment_id: The ID of the appointment to complete
            result_data: The inspection result data
            current_user: The current authenticated user (must be inspector)

        Returns:
            The updated appointment

        Raises:
            HTTPException: If validation fails or operation is not permitted
        """
        # Get and validate inspector
        inspector = self._get_inspector(current_user)

        # Get and validate appointment
        appointment = self._get_appointment(appointment_id)

        # Validate inspector assignment and appointment status
        self._validate_completion_permissions(appointment, inspector)
        self._validate_appointment_status(appointment)

        # Get check item templates
        templates = self._get_check_templates()

        # Create inspection result
        inspection_result = self._create_inspection_result(appointment, result_data)

        # Create item checks
        self._create_item_checks(inspection_result, templates, result_data.item_scores)

        # Update annual inspection status
        self._update_annual_inspection_status(appointment, inspection_result, result_data.total_score)

        # Mark appointment as completed
        appointment.status = AppointmentStatus.COMPLETED

        # Commit all changes
        self.db.commit()
        self.db.refresh(appointment)

        return appointment

    def create(
        self,
        appointment_data: AppointmentCreate,
        current_user: User
    ) -> Appointment:
        """
        Create a new appointment.

        Args:
            appointment_data: The appointment creation data
            current_user: The current authenticated user

        Returns:
            The created appointment

        Raises:
            HTTPException: If validation fails or operation is not permitted
        """
        # Validate user role
        if current_user.role == UserRole.INSPECTOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los inspectores no pueden crear turnos"
            )

        # Verify vehicle exists
        vehicle = self._get_vehicle(appointment_data.vehicle_id)

        # Check ownership for clients
        if current_user.role == UserRole.CLIENT and vehicle.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para crear turnos para este vehículo"
            )

        # Get or create annual inspection for current year
        annual = self._get_or_create_annual_inspection(
            vehicle_id=vehicle.id,
            annual_inspection_id=appointment_data.annual_inspection_id
        )

        # Verify inspector if specified
        inspector_id = None
        if appointment_data.inspector_id:
            inspector_id = self._validate_inspector_assignment(
                appointment_data.inspector_id,
                current_user
            )

        # Determine date_time: from slot_id or direct date_time
        appointment_datetime = None
        if appointment_data.slot_id:
            # Get and book the slot
            slot = self._get_and_book_slot(appointment_data.slot_id)
            appointment_datetime = slot.start_time
        elif appointment_data.date_time:
            appointment_datetime = appointment_data.date_time
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe proporcionar slot_id o date_time"
            )

        # Create appointment
        new_appointment = Appointment(
            id=generate_uuid(),
            annual_inspection_id=annual.id,
            vehicle_id=appointment_data.vehicle_id,
            inspector_id=inspector_id,
            created_by_user_id=current_user.id,
            created_channel=CreatedChannel.CLIENT_PORTAL if current_user.role == UserRole.CLIENT else CreatedChannel.ADMIN_PANEL,
            date_time=appointment_datetime,
            status=AppointmentStatus.CONFIRMED,
            confirmation_token=f"CONF-{generate_uuid()[:8]}",
        )

        self.db.add(new_appointment)
        self.db.commit()
        self.db.refresh(new_appointment)

        return new_appointment

    def list(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[AppointmentStatus] = None,
        vehicle_id: Optional[str] = None,
        inspector_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Tuple[List[Appointment], int]:
        """
        List appointments with pagination and filters.

        Args:
            current_user: The current authenticated user
            page: Page number (1-indexed)
            page_size: Number of results per page
            status_filter: Filter by appointment status
            vehicle_id: Filter by vehicle ID
            inspector_id: Filter by inspector ID (admin only)
            from_date: Filter appointments from this date
            to_date: Filter appointments until this date

        Returns:
            Tuple of (list of appointments, total count)

        Raises:
            HTTPException: If user doesn't have permission
        """
        # Build base query with joins
        query = self.db.query(Appointment).join(Vehicle).join(User, Vehicle.owner_id == User.id)

        # Apply role-based filtering
        if current_user.role == UserRole.CLIENT:
            # Clients only see appointments for their vehicles
            query = query.filter(Vehicle.owner_id == current_user.id)
        elif current_user.role == UserRole.INSPECTOR:
            # Inspectors only see their assigned appointments
            inspector = self._get_inspector(current_user)
            query = query.filter(Appointment.inspector_id == inspector.id)

        # Apply additional filters
        if status_filter:
            query = query.filter(Appointment.status == status_filter)
        if vehicle_id:
            query = query.filter(Appointment.vehicle_id == vehicle_id)
        if inspector_id and current_user.role == UserRole.ADMIN:
            query = query.filter(Appointment.inspector_id == inspector_id)
        if from_date:
            query = query.filter(Appointment.date_time >= from_date)
        if to_date:
            query = query.filter(Appointment.date_time <= to_date)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        appointments = query.order_by(Appointment.date_time.desc()).offset(offset).limit(page_size).all()

        return appointments, total

    def get(self, appointment_id: str, current_user: User) -> Appointment:
        """
        Get appointment details by ID.

        Args:
            appointment_id: The ID of the appointment
            current_user: The current authenticated user

        Returns:
            The appointment

        Raises:
            HTTPException: If appointment not found or user doesn't have permission
        """
        appointment = self._get_appointment(appointment_id)

        # Check access permissions
        if current_user.role == UserRole.CLIENT:
            if appointment.vehicle.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para ver este turno"
                )
        elif current_user.role == UserRole.INSPECTOR:
            inspector = self._get_inspector(current_user)
            if appointment.inspector_id != inspector.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para ver este turno"
                )

        return appointment

    def update(
        self,
        appointment_id: str,
        appointment_data: AppointmentUpdate,
        current_user: User
    ) -> Appointment:
        """
        Update appointment details.

        Args:
            appointment_id: The ID of the appointment to update
            appointment_data: The update data
            current_user: The current authenticated user

        Returns:
            The updated appointment

        Raises:
            HTTPException: If validation fails or operation is not permitted
        """
        # Validate user role
        if current_user.role == UserRole.INSPECTOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los inspectores no pueden modificar turnos"
            )

        appointment = self._get_appointment(appointment_id)

        # Check access permissions
        if current_user.role == UserRole.CLIENT:
            self._validate_client_update_permissions(appointment, current_user, appointment_data)

        # Update fields
        if appointment_data.date_time is not None:
            # Free the old slot if it exists
            old_datetime = appointment.date_time
            self._free_slot_if_exists(old_datetime)

            # Try to book the new slot if it exists
            new_datetime = appointment_data.date_time
            slot = self.db.query(AvailabilitySlot).filter(
                AvailabilitySlot.start_time == new_datetime
            ).first()

            if slot:
                if slot.is_booked:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="El slot seleccionado ya está reservado"
                    )
                slot.is_booked = True
                self.db.flush()

            appointment.date_time = new_datetime

        if appointment_data.inspector_id is not None:
            inspector_id = self._validate_inspector_assignment(
                appointment_data.inspector_id,
                current_user
            )
            appointment.inspector_id = inspector_id

        if appointment_data.status is not None:
            if current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Solo los administradores pueden cambiar el estado"
                )
            appointment.status = appointment_data.status

        self.db.commit()
        self.db.refresh(appointment)

        return appointment

    def cancel(self, appointment_id: str, current_user: User) -> None:
        """
        Cancel an appointment.

        Args:
            appointment_id: The ID of the appointment to cancel
            current_user: The current authenticated user

        Raises:
            HTTPException: If validation fails or operation is not permitted
        """
        # Validate user role
        if current_user.role == UserRole.INSPECTOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los inspectores no pueden cancelar turnos"
            )

        appointment = self._get_appointment(appointment_id)

        # Check access permissions
        if current_user.role == UserRole.CLIENT:
            if appointment.vehicle.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para cancelar este turno"
                )
            # Clients cannot cancel completed appointments
            if appointment.status == AppointmentStatus.COMPLETED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede cancelar un turno completado"
                )

        # Already cancelled
        if appointment.status == AppointmentStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El turno ya está cancelado"
            )

        # Free the slot if it exists
        self._free_slot_if_exists(appointment.date_time)

        appointment.status = AppointmentStatus.CANCELLED
        self.db.commit()

    def get_available_slots(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[AvailabilitySlot]:
        """
        Get available time slots for appointments.

        Args:
            from_date: Filter slots from this date
            to_date: Filter slots until this date

        Returns:
            List of available slots
        """
        query = self.db.query(AvailabilitySlot).filter(AvailabilitySlot.is_booked == False)

        if from_date:
            query = query.filter(AvailabilitySlot.start_time >= from_date)
        if to_date:
            query = query.filter(AvailabilitySlot.end_time <= to_date)

        # Only show future slots
        query = query.filter(AvailabilitySlot.start_time > datetime.now(timezone.utc))

        slots = query.order_by(AvailabilitySlot.start_time.asc()).limit(100).all()

        return slots

    # Private helper methods

    def _get_inspector(self, user: User) -> Inspector:
        """Get inspector profile for the current user."""
        inspector = self.db.query(Inspector).filter(Inspector.user_id == user.id).first()
        if not inspector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inspector no encontrado"
            )
        return inspector

    def _get_appointment(self, appointment_id: str) -> Appointment:
        """Get appointment by ID."""
        appointment = self.db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Turno no encontrado"
            )
        return appointment

    def _validate_completion_permissions(self, appointment: Appointment, inspector: Inspector) -> None:
        """Validate that the inspector is assigned to this appointment."""
        if appointment.inspector_id != inspector.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Este turno no está asignado a ti"
            )

    def _validate_appointment_status(self, appointment: Appointment) -> None:
        """Validate that the appointment can be completed."""
        if appointment.status != AppointmentStatus.CONFIRMED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se pueden completar turnos confirmados"
            )

    def _get_check_templates(self) -> List[CheckItemTemplate]:
        """Get all check item templates in order."""
        templates = self.db.query(CheckItemTemplate).order_by(CheckItemTemplate.ordinal.asc()).all()
        if len(templates) != 8:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Plantillas de chequeo no configuradas correctamente"
            )
        return templates

    def _create_inspection_result(
        self,
        appointment: Appointment,
        result_data: CompleteAppointmentRequest
    ) -> InspectionResult:
        """Create an inspection result record."""
        inspection_result = InspectionResult(
            id=generate_uuid(),
            annual_inspection_id=appointment.annual_inspection_id,
            appointment_id=appointment.id,
            total_score=result_data.total_score,
            owner_observation=result_data.owner_observation,
        )
        self.db.add(inspection_result)
        self.db.flush()
        return inspection_result

    def _create_item_checks(
        self,
        inspection_result: InspectionResult,
        templates: List[CheckItemTemplate],
        item_scores: List[int]
    ) -> None:
        """Create item check records for each template."""
        for template, score in zip(templates, item_scores):
            item_check = ItemCheck(
                id=generate_uuid(),
                inspection_result_id=inspection_result.id,
                check_item_template_id=template.id,
                score=score,
                observation="Chequeo realizado" if score >= 5 else "Requiere atención",
            )
            self.db.add(item_check)

    def _update_annual_inspection_status(
        self,
        appointment: Appointment,
        inspection_result: InspectionResult,
        total_score: int
    ) -> None:
        """Update the annual inspection with the result and determine pass/fail status."""
        annual = self.db.query(AnnualInspection).filter(
            AnnualInspection.id == appointment.annual_inspection_id
        ).first()

        if annual:
            annual.current_result_id = inspection_result.id
            annual.attempt_count += 1
            # Determine pass/fail (passing score is 40 or higher)
            annual.status = AnnualStatus.PASSED if total_score >= 40 else AnnualStatus.FAILED

    def _get_vehicle(self, vehicle_id: str) -> Vehicle:
        """Get vehicle by ID."""
        vehicle = self.db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehículo no encontrado"
            )
        return vehicle

    def _get_annual_inspection(self, annual_inspection_id: str) -> AnnualInspection:
        """Get annual inspection by ID."""
        annual = self.db.query(AnnualInspection).filter(
            AnnualInspection.id == annual_inspection_id
        ).first()
        if not annual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inspección anual no encontrada"
            )
        return annual

    def _validate_inspector_assignment(self, inspector_id: str, current_user: User) -> str:
        """Validate inspector assignment (admin only)."""
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los administradores pueden asignar inspectores"
            )
        inspector = self.db.query(Inspector).filter(
            Inspector.id == inspector_id,
            Inspector.active == True
        ).first()
        if not inspector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inspector no encontrado o inactivo"
            )
        return inspector_id

    def _validate_client_update_permissions(
        self,
        appointment: Appointment,
        current_user: User,
        appointment_data: AppointmentUpdate
    ) -> None:
        """Validate that a client can perform the requested update."""
        if appointment.vehicle.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para modificar este turno"
            )
        # Clients cannot update completed or cancelled appointments
        if appointment.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede modificar un turno completado o cancelado"
            )
        # Clients can only update date_time
        if appointment_data.inspector_id is not None or appointment_data.status is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo puedes cambiar la fecha del turno"
            )

    def _get_or_create_annual_inspection(
        self,
        vehicle_id: str,
        annual_inspection_id: Optional[str] = None
    ) -> AnnualInspection:
        """
        Get or create an annual inspection for the current year.

        Args:
            vehicle_id: The vehicle ID
            annual_inspection_id: Optional annual inspection ID (for backwards compatibility)

        Returns:
            The annual inspection for the current year

        Raises:
            HTTPException: If the annual inspection for the current year is already approved
        """
        current_year = datetime.now().year

        # If annual_inspection_id is provided, verify it and use it
        if annual_inspection_id:
            annual = self._get_annual_inspection(annual_inspection_id)
            if annual.vehicle_id != vehicle_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La inspección anual no corresponde al vehículo especificado"
                )
            return annual

        # Check if an annual inspection exists for the current year
        annual = self.db.query(AnnualInspection).filter(
            AnnualInspection.vehicle_id == vehicle_id,
            AnnualInspection.year == current_year
        ).first()

        # If it exists and is PASSED, reject the appointment creation
        if annual and annual.status == AnnualStatus.PASSED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La inspección anual para este año ya fue aprobada"
            )

        # If it exists but is not PASSED, return it
        if annual:
            return annual

        # If it doesn't exist, create it
        new_annual = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=vehicle_id,
            year=current_year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        self.db.add(new_annual)
        self.db.flush()  # Flush to get the ID

        return new_annual

    def _get_and_book_slot(self, slot_id: str) -> AvailabilitySlot:
        """
        Get a slot and mark it as booked.

        Args:
            slot_id: The slot ID

        Returns:
            The booked slot

        Raises:
            HTTPException: If slot not found or already booked
        """
        slot = self.db.query(AvailabilitySlot).filter(AvailabilitySlot.id == slot_id).first()
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot no encontrado"
            )

        if slot.is_booked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este slot ya está reservado"
            )

        # Mark as booked
        slot.is_booked = True
        self.db.flush()

        return slot

    def _free_slot_if_exists(self, date_time: datetime) -> None:
        """
        Free a slot if it exists for the given datetime.

        Args:
            date_time: The datetime to match against slot start_time
        """
        slot = self.db.query(AvailabilitySlot).filter(
            AvailabilitySlot.start_time == date_time
        ).first()

        if slot and slot.is_booked:
            slot.is_booked = False
            self.db.flush()
