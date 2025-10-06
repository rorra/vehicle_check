from typing import Optional
from fastapi import APIRouter, Depends, Query, Path
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas.inspection_result import (
    InspectionResultDetail,
    InspectionResultListItem,
    InspectionResultListResponse,
    ItemCheckDetail,
)
from app.services.inspection_result_service import InspectionResultService

router = APIRouter()


@router.get("/", response_model=InspectionResultListResponse)
def list_inspection_results(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de resultados por página"),
    year: Optional[int] = Query(None, description="Filtrar por año"),
    vehicle_id: Optional[str] = Query(None, description="Filtrar por vehículo"),
    passed_only: Optional[bool] = Query(None, description="Filtrar solo aprobados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List inspection results with pagination and filters.

    - CLIENT: Can only see results for their own vehicles
    - INSPECTOR: Can see all results
    - ADMIN: Can see all results
    """
    service = InspectionResultService(db)
    results, total = service.list(current_user, page, page_size, year, vehicle_id, passed_only)

    # Build response
    result_list = []
    for result in results:
        annual = result.annual_inspection
        result_list.append(InspectionResultListItem(
            id=result.id,
            annual_inspection_id=result.annual_inspection_id,
            total_score=result.total_score,
            created_at=result.created_at,
            vehicle_plate=annual.vehicle.plate_number,
            year=annual.year,
            passed=result.total_score >= 40,
        ))

    return InspectionResultListResponse(
        results=result_list,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{result_id}", response_model=InspectionResultDetail)
def get_inspection_result(
    result_id: str = Path(..., description="ID único del resultado de inspección"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed inspection result by ID.

    - CLIENT: Can only access results for their own vehicles
    - INSPECTOR: Can access any result
    - ADMIN: Can access any result
    """
    service = InspectionResultService(db)
    result = service.get(result_id, current_user)

    # Get item checks with template details
    item_checks = service.get_item_checks(result.id)

    item_check_details = []
    for item_check in item_checks:
        item_check_details.append(ItemCheckDetail(
            id=item_check.id,
            check_item_template_id=item_check.check_item_template_id,
            template_code=item_check.template.code,
            template_description=item_check.template.description,
            template_ordinal=item_check.template.ordinal,
            score=item_check.score,
            observation=item_check.observation,
        ))

    # Get inspector name
    inspector_name = service.get_inspector_name(result.appointment_id)

    return InspectionResultDetail(
        id=result.id,
        annual_inspection_id=result.annual_inspection_id,
        appointment_id=result.appointment_id,
        total_score=result.total_score,
        owner_observation=result.owner_observation,
        created_at=result.created_at,
        updated_at=result.updated_at,
        item_checks=item_check_details,
        vehicle_plate=result.annual_inspection.vehicle.plate_number,
        vehicle_make=result.annual_inspection.vehicle.make,
        vehicle_model=result.annual_inspection.vehicle.model,
        inspector_name=inspector_name,
        inspection_date=result.appointment.date_time,
        passed=result.total_score >= 40,
    )


@router.get("/annual-inspection/{annual_inspection_id}", response_model=list[InspectionResultListItem])
def get_results_by_annual_inspection(
    annual_inspection_id: str = Path(..., description="ID de la inspección anual"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all inspection results for a specific annual inspection.

    - CLIENT: Can only access results for their own vehicles
    - INSPECTOR: Can access any results
    - ADMIN: Can access any results
    """
    service = InspectionResultService(db)
    results = service.get_by_annual_inspection(annual_inspection_id, current_user)

    # Build response
    result_list = []
    for result in results:
        annual = result.annual_inspection
        result_list.append(InspectionResultListItem(
            id=result.id,
            annual_inspection_id=result.annual_inspection_id,
            total_score=result.total_score,
            created_at=result.created_at,
            vehicle_plate=annual.vehicle.plate_number,
            year=annual.year,
            passed=result.total_score >= 40,
        ))

    return result_list
