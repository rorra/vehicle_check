from fastapi import APIRouter, Depends, status, Path
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models import User
from app.schemas.check_item import (
    CheckItemTemplateCreate,
    CheckItemTemplateUpdate,
    CheckItemTemplateResponse,
)
from app.services.check_item_service import CheckItemService

router = APIRouter()


@router.get("/", response_model=list[CheckItemTemplateResponse])
def list_check_item_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all check item templates ordered by ordinal.

    Accessible by all authenticated users.
    """
    service = CheckItemService(db)
    return service.list()


@router.get("/{template_id}", response_model=CheckItemTemplateResponse)
def get_check_item_template(
    template_id: str = Path(..., description="ID único de la plantilla"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get check item template by ID.

    Accessible by all authenticated users.
    """
    service = CheckItemService(db)
    return service.get(template_id)


@router.post("/", response_model=CheckItemTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_check_item_template(
    template_data: CheckItemTemplateCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new check item template.

    Only accessible by ADMIN.
    """
    service = CheckItemService(db)
    return service.create(template_data.code, template_data.description, template_data.ordinal)


@router.put("/{template_id}", response_model=CheckItemTemplateResponse)
def update_check_item_template(
    template_id: str = Path(..., description="ID único de la plantilla a actualizar"),
    template_data: CheckItemTemplateUpdate = ...,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update check item template.

    Only accessible by ADMIN.
    """
    service = CheckItemService(db)
    return service.update(template_id, template_data.code, template_data.description, template_data.ordinal)


@router.delete("/{template_id}", status_code=status.HTTP_200_OK)
def delete_check_item_template(
    template_id: str = Path(..., description="ID único de la plantilla a eliminar"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a check item template.

    Only accessible by ADMIN.
    Warning: This will affect all existing inspection results that reference this template.
    """
    service = CheckItemService(db)
    service.delete(template_id)
    return {"message": "Plantilla de chequeo eliminada exitosamente"}
