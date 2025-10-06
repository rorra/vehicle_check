from pydantic import BaseModel, field_validator, ConfigDict, Field
from typing import Optional
from datetime import datetime


class InspectorCreate(BaseModel):
    """Schema for creating a new inspector."""
    user_id: str = Field(
        ...,
        description="ID del usuario que será inspector",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    employee_id: str = Field(
        ...,
        description="ID de empleado/legajo del inspector",
        max_length=50,
        examples=["INS-001", "EMP-12345"]
    )

    @field_validator("employee_id")
    @classmethod
    def validate_employee_id(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("El ID de empleado no puede estar vacío")
        return v.strip().upper()


class InspectorUpdate(BaseModel):
    """Schema for updating an inspector."""
    employee_id: Optional[str] = Field(
        None,
        description="Nuevo ID de empleado/legajo",
        max_length=50,
        examples=["INS-002"]
    )
    active: Optional[bool] = Field(
        None,
        description="Estado activo del inspector",
        examples=[True, False]
    )

    @field_validator("employee_id")
    @classmethod
    def validate_employee_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("El ID de empleado no puede estar vacío")
            return v.strip().upper()
        return v


class InspectorResponse(BaseModel):
    """Schema for inspector response."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID único del inspector")
    user_id: str = Field(..., description="ID del usuario")
    employee_id: str = Field(..., description="ID de empleado/legajo")
    active: bool = Field(..., description="Si el inspector está activo")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")


class InspectorWithUser(InspectorResponse):
    """Schema for inspector response with user details."""
    user_name: str = Field(..., description="Nombre del usuario")
    user_email: str = Field(..., description="Email del usuario")
    user_is_active: bool = Field(..., description="Si el usuario está activo")


class InspectorListResponse(BaseModel):
    """Schema for paginated inspector list response."""
    inspectors: list[InspectorWithUser] = Field(..., description="Lista de inspectores")
    total: int = Field(..., description="Total de inspectores encontrados")
    page: int = Field(..., description="Número de página actual")
    page_size: int = Field(..., description="Cantidad de resultados por página")
