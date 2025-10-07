from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models import User, UserRole
from app.schemas.appointment import AvailableSlotResponse, AvailableSlotCreate
from app.services.available_slot_service import AvailableSlotService

router = APIRouter()


@router.post("/", response_model=AvailableSlotResponse, status_code=status.HTTP_201_CREATED)
def create_slot(
    slot_data: AvailableSlotCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new availability slot.

    Only accessible by ADMIN.
    """
    service = AvailableSlotService(db)
    return service.create(slot_data)


@router.get("/", response_model=list[AvailableSlotResponse])
def list_slots(
    from_date: Optional[datetime] = Query(None, description="Fecha de inicio"),
    to_date: Optional[datetime] = Query(None, description="Fecha de fin"),
    include_booked: bool = Query(False, description="Incluir slots reservados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List availability slots.

    Accessible by all authenticated users.
    Clients can only see available (non-booked) slots.
    Admins can see all slots including booked ones if include_booked=True.
    """
    service = AvailableSlotService(db)

    # Only admins can see booked slots
    if include_booked and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden ver slots reservados"
        )

    return service.list(from_date, to_date, include_booked)


@router.get("/{slot_id}", response_model=AvailableSlotResponse)
def get_slot(
    slot_id: str = Path(..., description="ID único del slot"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get slot details by ID.

    Accessible by all authenticated users.
    """
    service = AvailableSlotService(db)
    return service.get(slot_id)


@router.delete("/{slot_id}", status_code=status.HTTP_200_OK)
def delete_slot(
    slot_id: str = Path(..., description="ID único del slot a eliminar"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a slot.

    Only accessible by ADMIN.
    Cannot delete booked slots.
    """
    service = AvailableSlotService(db)
    service.delete(slot_id)
    return {"message": "Slot eliminado exitosamente"}
