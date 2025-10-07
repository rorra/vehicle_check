from typing import Optional
from fastapi import APIRouter, Depends, status, Query, Path
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models import User, UserRole
from app.schemas.user import (
    UserUpdate,
    UserListResponse,
    ChangePasswordRequest,
)
from app.schemas.auth import UserResponse, UserRegister
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile.

    Accessible by any authenticated user.
    """
    service = UserService(db)
    return service.get_current_user(current_user)


@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile.

    Users can update their own name and email, but not role or active status.
    """
    service = UserService(db)
    return service.update_current_user(current_user, user_data.name, user_data.email, user_data.role,
                                       user_data.is_active)


@router.post("/me/change-password", status_code=status.HTTP_200_OK)
def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password.

    Requires current password for verification.
    """
    service = UserService(db)
    service.change_password(current_user, password_data.current_password, password_data.new_password)
    return {"message": "Contraseña cambiada exitosamente. Por favor, inicia sesión nuevamente."}


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserRegister,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new user (ADMIN only).

    Allows administrators to create users with any role.
    """
    service = UserService(db)
    return service.create(
        name=user_data.name,
        email=user_data.email,
        password=user_data.password,
        role=user_data.role,
        is_active=True
    )


@router.get("/", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de resultados por página"),
    role: Optional[UserRole] = Query(None, description="Filtrar por rol"),
    active_only: Optional[bool] = Query(None, description="Filtrar solo usuarios activos"),
    search: Optional[str] = Query(None, description="Buscar por nombre o email"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all users with pagination and filters.

    Only accessible by ADMIN.
    """
    service = UserService(db)
    users, total = service.list(page, page_size, role, active_only, search)

    return UserListResponse(
        users=users,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str = Path(..., description="ID único del usuario"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get user details by ID.

    Only accessible by ADMIN.
    """
    service = UserService(db)
    return service.get(user_id)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str = Path(..., description="ID único del usuario a actualizar"),
    user_data: UserUpdate = ...,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update user details.

    Only accessible by ADMIN.
    """
    service = UserService(db)
    return service.update(user_id, user_data.name, user_data.email, user_data.role, user_data.is_active)


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: str = Path(..., description="ID único del usuario a eliminar"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a user.

    Only accessible by ADMIN.
    Note: This will cascade delete all related data (vehicles, appointments, etc.).
    """
    service = UserService(db)
    service.delete(user_id, current_user.id)
    return {"message": "Usuario eliminado exitosamente"}
