from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from datetime import datetime, timezone
from app.core.database import get_db
from app.core.deps import get_current_user, require_inspector, require_admin
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
    AvailabilitySlot,
    InspectionResult,
    CheckItemTemplate,
    ItemCheck,
    generate_uuid,
)
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AppointmentWithDetails,
    AppointmentListResponse,
    AvailableSlotResponse,
    CompleteAppointmentRequest,
)
from app.services.appointment_service import AppointmentService

router = APIRouter()


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new appointment.

    - CLIENT: Can create appointments for their own vehicles
    - ADMIN: Can create appointments for any vehicle and assign inspectors
    - INSPECTOR: Cannot create appointments
    """
    service = AppointmentService(db)
    return service.create(appointment_data, current_user)


@router.get("/", response_model=AppointmentListResponse)
def list_appointments(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de resultados por página"),
    status_filter: Optional[AppointmentStatus] = Query(None, description="Filtrar por estado"),
    vehicle_id: Optional[str] = Query(None, description="Filtrar por vehículo"),
    inspector_id: Optional[str] = Query(None, description="Filtrar por inspector"),
    from_date: Optional[datetime] = Query(None, description="Filtrar desde fecha"),
    to_date: Optional[datetime] = Query(None, description="Filtrar hasta fecha"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List appointments with pagination and filters.

    - CLIENT: Can only see appointments for their own vehicles
    - INSPECTOR: Can see their assigned appointments
    - ADMIN: Can see all appointments
    """
    service = AppointmentService(db)
    appointments, total = service.list(
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        vehicle_id=vehicle_id,
        inspector_id=inspector_id,
        from_date=from_date,
        to_date=to_date
    )

    # Build response with details
    result = []
    for appointment in appointments:
        inspector_name = None
        if appointment.inspector_id:
            inspector = db.query(Inspector).join(User).filter(Inspector.id == appointment.inspector_id).first()
            if inspector:
                inspector_name = inspector.user.name

        result.append(AppointmentWithDetails(
            id=appointment.id,
            annual_inspection_id=appointment.annual_inspection_id,
            vehicle_id=appointment.vehicle_id,
            inspector_id=appointment.inspector_id,
            created_by_user_id=appointment.created_by_user_id,
            created_channel=appointment.created_channel,
            date_time=appointment.date_time,
            status=appointment.status,
            confirmation_token=appointment.confirmation_token,
            created_at=appointment.created_at,
            updated_at=appointment.updated_at,
            vehicle_plate=appointment.vehicle.plate_number,
            vehicle_make=appointment.vehicle.make,
            vehicle_model=appointment.vehicle.model,
            owner_name=appointment.vehicle.owner.name,
            owner_email=appointment.vehicle.owner.email,
            inspector_name=inspector_name,
        ))

    return AppointmentListResponse(
        appointments=result,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/available-slots", response_model=list[AvailableSlotResponse])
def get_available_slots(
    from_date: Optional[datetime] = Query(None, description="Fecha de inicio"),
    to_date: Optional[datetime] = Query(None, description="Fecha de fin"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get available time slots for appointments.

    Accessible by all authenticated users.
    """
    service = AppointmentService(db)
    return service.get_available_slots(from_date, to_date)


@router.get("/{appointment_id}", response_model=AppointmentWithDetails)
def get_appointment(
    appointment_id: str = Path(..., description="ID único del turno"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get appointment details by ID.

    - CLIENT: Can only access appointments for their own vehicles
    - INSPECTOR: Can access their assigned appointments
    - ADMIN: Can access any appointment
    """
    service = AppointmentService(db)
    appointment = service.get(appointment_id, current_user)

    # Build response with details
    inspector_name = None
    if appointment.inspector_id:
        inspector = db.query(Inspector).join(User).filter(Inspector.id == appointment.inspector_id).first()
        if inspector:
            inspector_name = inspector.user.name

    return AppointmentWithDetails(
        id=appointment.id,
        annual_inspection_id=appointment.annual_inspection_id,
        vehicle_id=appointment.vehicle_id,
        inspector_id=appointment.inspector_id,
        created_by_user_id=appointment.created_by_user_id,
        created_channel=appointment.created_channel,
        date_time=appointment.date_time,
        status=appointment.status,
        confirmation_token=appointment.confirmation_token,
        created_at=appointment.created_at,
        updated_at=appointment.updated_at,
        vehicle_plate=appointment.vehicle.plate_number,
        vehicle_make=appointment.vehicle.make,
        vehicle_model=appointment.vehicle.model,
        owner_name=appointment.vehicle.owner.name,
        owner_email=appointment.vehicle.owner.email,
        inspector_name=inspector_name,
    )


@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: str = Path(..., description="ID único del turno a actualizar"),
    appointment_data: AppointmentUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update appointment details.

    - CLIENT: Can reschedule their own appointments (if not completed/cancelled)
    - ADMIN: Can update any appointment (reschedule, reassign inspector, change status)
    - INSPECTOR: Cannot update appointments
    """
    service = AppointmentService(db)
    return service.update(appointment_id, appointment_data, current_user)


@router.delete("/{appointment_id}", status_code=status.HTTP_200_OK)
def cancel_appointment(
    appointment_id: str = Path(..., description="ID único del turno a cancelar"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel an appointment.

    - CLIENT: Can cancel their own appointments (if not completed)
    - ADMIN: Can cancel any appointment
    - INSPECTOR: Cannot cancel appointments
    """
    service = AppointmentService(db)
    service.cancel(appointment_id, current_user)
    return {"message": "Turno cancelado exitosamente"}


@router.post("/{appointment_id}/complete", response_model=AppointmentResponse)
def complete_appointment(
    appointment_id: str = Path(..., description="ID único del turno a completar"),
    result_data: CompleteAppointmentRequest = ...,
    current_user: User = Depends(require_inspector),
    db: Session = Depends(get_db)
):
    """
    Complete an appointment and record inspection results.

    Only accessible by INSPECTOR assigned to the appointment.
    """
    service = AppointmentService(db)
    return service.complete_with_inspection(appointment_id, result_data, current_user)
