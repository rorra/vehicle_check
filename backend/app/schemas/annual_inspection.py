from pydantic import BaseModel, field_validator, ConfigDict, Field
from typing import Optional
from datetime import datetime
from app.models import AnnualStatus


class AnnualInspectionCreate(BaseModel):
    """Schema for creating a new annual inspection."""
    vehicle_id: str = Field(
        ...,
        description="ID del vehículo",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    year: int = Field(
        ...,
        description="Año de la inspección",
        ge=2000,
        le=2100,
        examples=[2024, 2025]
    )

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        current_year = datetime.now().year
        if v < current_year - 1 or v > current_year + 1:
            raise ValueError(f"El año debe estar entre {current_year - 1} y {current_year + 1}")
        return v


class AnnualInspectionUpdate(BaseModel):
    """Schema for updating an annual inspection."""
    status: Optional[AnnualStatus] = Field(
        None,
        description="Nuevo estado de la inspección",
        examples=["PENDING"]
    )


class AnnualInspectionResponse(BaseModel):
    """Schema for annual inspection response."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID único de la inspección anual")
    vehicle_id: str = Field(..., description="ID del vehículo")
    year: int = Field(..., description="Año de la inspección")
    status: AnnualStatus = Field(..., description="Estado de la inspección")
    attempt_count: int = Field(..., description="Número de intentos realizados")
    current_result_id: Optional[str] = Field(None, description="ID del resultado actual")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")


class AnnualInspectionWithDetails(AnnualInspectionResponse):
    """Schema for annual inspection with vehicle details."""
    vehicle_plate: str = Field(..., description="Matrícula del vehículo")
    vehicle_make: Optional[str] = Field(None, description="Marca del vehículo")
    vehicle_model: Optional[str] = Field(None, description="Modelo del vehículo")
    vehicle_year: Optional[int] = Field(None, description="Año del vehículo")
    owner_name: str = Field(..., description="Nombre del propietario")
    owner_email: str = Field(..., description="Email del propietario")
    total_appointments: int = Field(..., description="Total de turnos asociados")
    last_appointment_date: Optional[datetime] = Field(None, description="Fecha del último turno")


class AnnualInspectionListResponse(BaseModel):
    """Schema for paginated annual inspection list response."""
    inspections: list[AnnualInspectionWithDetails] = Field(..., description="Lista de inspecciones anuales")
    total: int = Field(..., description="Total de inspecciones encontradas")
    page: int = Field(..., description="Número de página actual")
    page_size: int = Field(..., description="Cantidad de resultados por página")
