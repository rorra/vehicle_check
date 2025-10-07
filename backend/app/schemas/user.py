from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, Field
from typing import Optional
from datetime import datetime
from app.models import UserRole


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = Field(
        None,
        description="Nuevo nombre del usuario",
        min_length=2,
        examples=["Juan Pérez"]
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Nuevo correo electrónico",
        examples=["juan@example.com"]
    )
    is_active: Optional[bool] = Field(
        None,
        description="Estado activo del usuario",
        examples=[True, False]
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        return v


class UserListItem(BaseModel):
    """Schema for user in list response."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID único del usuario")
    name: str = Field(..., description="Nombre completo del usuario")
    email: str = Field(..., description="Correo electrónico")
    role: UserRole = Field(..., description="Rol del usuario")
    is_active: bool = Field(..., description="Si el usuario está activo")
    created_at: datetime = Field(..., description="Fecha de creación")
    last_login: Optional[datetime] = Field(None, description="Último inicio de sesión")


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""
    users: list[UserListItem] = Field(..., description="Lista de usuarios")
    total: int = Field(..., description="Total de usuarios encontrados")
    page: int = Field(..., description="Número de página actual")
    page_size: int = Field(..., description="Cantidad de resultados por página")


class ChangePasswordRequest(BaseModel):
    """Schema for changing user password."""
    current_password: str = Field(
        ...,
        description="Contraseña actual",
        examples=["oldpassword123"]
    )
    new_password: str = Field(
        ...,
        description="Nueva contraseña (mínimo 6 caracteres)",
        min_length=6,
        examples=["newpassword123"]
    )

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v
