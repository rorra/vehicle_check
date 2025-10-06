from typing import Optional
from fastapi import APIRouter, Depends, status, Query, Path
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import require_admin
from app.models import User
from app.schemas.inspector import (
    InspectorCreate,
    InspectorUpdate,
    InspectorResponse,
    InspectorWithUser,
    InspectorListResponse,
)
from app.services.inspector_service import InspectorService

router = APIRouter()


@router.post("/", response_model=InspectorResponse, status_code=status.HTTP_201_CREATED)
def create_inspector(
    inspector_data: InspectorCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new inspector profile.

    Only accessible by ADMIN.
    """
    service = InspectorService(db)
    return service.create(inspector_data.user_id, inspector_data.employee_id)


@router.get("/", response_model=InspectorListResponse)
def list_inspectors(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de resultados por página"),
    active_only: Optional[bool] = Query(None, description="Filtrar solo inspectores activos"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all inspectors with pagination.

    Only accessible by ADMIN.
    """
    service = InspectorService(db)
    inspectors, total = service.list(page, page_size, active_only)

    # Build response with user details
    result = []
    for inspector in inspectors:
        result.append(InspectorWithUser(
            id=inspector.id,
            user_id=inspector.user_id,
            employee_id=inspector.employee_id,
            active=inspector.active,
            created_at=inspector.created_at,
            updated_at=inspector.updated_at,
            user_name=inspector.user.name,
            user_email=inspector.user.email,
            user_is_active=inspector.user.is_active,
        ))

    return InspectorListResponse(
        inspectors=result,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{inspector_id}", response_model=InspectorWithUser)
def get_inspector(
    inspector_id: str = Path(..., description="ID único del inspector"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get inspector details by ID.

    Only accessible by ADMIN.
    """
    service = InspectorService(db)
    inspector = service.get(inspector_id)

    return InspectorWithUser(
        id=inspector.id,
        user_id=inspector.user_id,
        employee_id=inspector.employee_id,
        active=inspector.active,
        created_at=inspector.created_at,
        updated_at=inspector.updated_at,
        user_name=inspector.user.name,
        user_email=inspector.user.email,
        user_is_active=inspector.user.is_active,
    )


@router.put("/{inspector_id}", response_model=InspectorResponse)
def update_inspector(
    inspector_id: str = Path(..., description="ID único del inspector a actualizar"),
    inspector_data: InspectorUpdate = ...,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update inspector details.

    Only accessible by ADMIN.
    """
    service = InspectorService(db)
    return service.update(inspector_id, inspector_data.employee_id, inspector_data.active)


@router.delete("/{inspector_id}", status_code=status.HTTP_200_OK)
def delete_inspector(
    inspector_id: str = Path(..., description="ID único del inspector a eliminar"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete an inspector profile.

    Only accessible by ADMIN.
    Note: This only deletes the inspector profile, not the user account.
    """
    service = InspectorService(db)
    service.delete(inspector_id)
    return {"message": "Inspector eliminado exitosamente"}
