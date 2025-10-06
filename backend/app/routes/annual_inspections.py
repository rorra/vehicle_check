from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models import (
    AnnualInspection,
    Vehicle,
    User,
    UserRole,
    AnnualStatus,
    Appointment,
    generate_uuid,
)
from app.schemas.annual_inspection import (
    AnnualInspectionCreate,
    AnnualInspectionUpdate,
    AnnualInspectionResponse,
    AnnualInspectionWithDetails,
    AnnualInspectionListResponse,
)
from app.services.annual_inspection_service import AnnualInspectionService

router = APIRouter()


@router.post("/", response_model=AnnualInspectionResponse, status_code=status.HTTP_201_CREATED)
def create_annual_inspection(
    inspection_data: AnnualInspectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new annual inspection.

    - CLIENT: Can create annual inspections for their own vehicles
    - ADMIN: Can create annual inspections for any vehicle
    - INSPECTOR: Cannot create annual inspections
    """
    service = AnnualInspectionService(db)
    return service.create(inspection_data, current_user)


@router.get("/", response_model=AnnualInspectionListResponse)
def list_annual_inspections(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de resultados por página"),
    status_filter: Optional[AnnualStatus] = Query(None, description="Filtrar por estado"),
    year: Optional[int] = Query(None, description="Filtrar por año"),
    vehicle_id: Optional[str] = Query(None, description="Filtrar por vehículo"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List annual inspections with pagination and filters.

    - CLIENT: Can only see inspections for their own vehicles
    - INSPECTOR: Can see all inspections
    - ADMIN: Can see all inspections
    """
    service = AnnualInspectionService(db)
    inspections, total = service.list(
        current_user=current_user,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        year=year,
        vehicle_id=vehicle_id
    )

    # Build response with details
    result = []
    for inspection in inspections:
        # Get appointment statistics
        stats = service.get_appointment_statistics(inspection.id)

        result.append(AnnualInspectionWithDetails(
            id=inspection.id,
            vehicle_id=inspection.vehicle_id,
            year=inspection.year,
            status=inspection.status,
            attempt_count=inspection.attempt_count,
            current_result_id=inspection.current_result_id,
            created_at=inspection.created_at,
            updated_at=inspection.updated_at,
            vehicle_plate=inspection.vehicle.plate_number,
            vehicle_make=inspection.vehicle.make,
            vehicle_model=inspection.vehicle.model,
            vehicle_year=inspection.vehicle.year,
            owner_name=inspection.vehicle.owner.name,
            owner_email=inspection.vehicle.owner.email,
            total_appointments=stats["total_appointments"],
            last_appointment_date=stats["last_appointment_date"],
        ))

    return AnnualInspectionListResponse(
        inspections=result,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{inspection_id}", response_model=AnnualInspectionWithDetails)
def get_annual_inspection(
    inspection_id: str = Path(..., description="ID único de la inspección anual"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get annual inspection details by ID.

    - CLIENT: Can only access inspections for their own vehicles
    - INSPECTOR: Can access any inspection
    - ADMIN: Can access any inspection
    """
    service = AnnualInspectionService(db)
    inspection = service.get(inspection_id, current_user)

    # Get appointment statistics
    stats = service.get_appointment_statistics(inspection.id)

    return AnnualInspectionWithDetails(
        id=inspection.id,
        vehicle_id=inspection.vehicle_id,
        year=inspection.year,
        status=inspection.status,
        attempt_count=inspection.attempt_count,
        current_result_id=inspection.current_result_id,
        created_at=inspection.created_at,
        updated_at=inspection.updated_at,
        vehicle_plate=inspection.vehicle.plate_number,
        vehicle_make=inspection.vehicle.make,
        vehicle_model=inspection.vehicle.model,
        vehicle_year=inspection.vehicle.year,
        owner_name=inspection.vehicle.owner.name,
        owner_email=inspection.vehicle.owner.email,
        total_appointments=stats["total_appointments"],
        last_appointment_date=stats["last_appointment_date"],
    )


@router.put("/{inspection_id}", response_model=AnnualInspectionResponse)
def update_annual_inspection(
    inspection_id: str = Path(..., description="ID único de la inspección a actualizar"),
    inspection_data: AnnualInspectionUpdate = ...,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update annual inspection status.

    Only accessible by ADMIN.
    """
    service = AnnualInspectionService(db)
    return service.update(inspection_id, inspection_data, current_user)


@router.delete("/{inspection_id}", status_code=status.HTTP_200_OK)
def delete_annual_inspection(
    inspection_id: str = Path(..., description="ID único de la inspección a eliminar"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete an annual inspection.

    Only accessible by ADMIN.
    Note: This will cascade delete all related appointments and results.
    """
    service = AnnualInspectionService(db)
    service.delete(inspection_id, current_user)
    return {"message": "Inspección anual eliminada exitosamente"}
