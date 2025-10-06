from pydantic import BaseModel, field_validator, ConfigDict, Field
from typing import Optional
from datetime import datetime


class VehicleCreate(BaseModel):
    """Schema for creating a new vehicle."""
    plate_number: str = Field(
        ...,
        description="Número de matrícula del vehículo",
        max_length=20,
        examples=["ABC123", "XYZ789"]
    )
    make: Optional[str] = Field(
        None,
        description="Marca del vehículo",
        max_length=60,
        examples=["Toyota", "Honda", "Ford"]
    )
    model: Optional[str] = Field(
        None,
        description="Modelo del vehículo",
        max_length=60,
        examples=["Corolla", "Civic", "Focus"]
    )
    year: Optional[int] = Field(
        None,
        description="Año del vehículo",
        ge=1900,
        le=2100,
        examples=[2020, 2021, 2022]
    )
    owner_id: Optional[str] = Field(
        None,
        description="ID del propietario (solo para ADMIN)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )

    @field_validator("plate_number")
    @classmethod
    def validate_plate_number(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("La matrícula no puede estar vacía")
        if len(v) > 20:
            raise ValueError("La matrícula no puede tener más de 20 caracteres")
        return v.strip().upper()

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v < 1900 or v > 2100:
                raise ValueError("El año debe estar entre 1900 y 2100")
        return v


class VehicleUpdate(BaseModel):
    """Schema for updating a vehicle."""
    plate_number: Optional[str] = Field(
        None,
        description="Nuevo número de matrícula",
        max_length=20,
        examples=["ABC123"]
    )
    make: Optional[str] = Field(
        None,
        description="Nueva marca del vehículo",
        max_length=60,
        examples=["Toyota"]
    )
    model: Optional[str] = Field(
        None,
        description="Nuevo modelo del vehículo",
        max_length=60,
        examples=["Corolla"]
    )
    year: Optional[int] = Field(
        None,
        description="Nuevo año del vehículo",
        ge=1900,
        le=2100,
        examples=[2021]
    )

    @field_validator("plate_number")
    @classmethod
    def validate_plate_number(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("La matrícula no puede estar vacía")
            if len(v) > 20:
                raise ValueError("La matrícula no puede tener más de 20 caracteres")
            return v.strip().upper()
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            if v < 1900 or v > 2100:
                raise ValueError("El año debe estar entre 1900 y 2100")
        return v


class VehicleResponse(BaseModel):
    """Schema for vehicle response."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID único del vehículo")
    plate_number: str = Field(..., description="Número de matrícula")
    make: Optional[str] = Field(None, description="Marca del vehículo")
    model: Optional[str] = Field(None, description="Modelo del vehículo")
    year: Optional[int] = Field(None, description="Año del vehículo")
    owner_id: str = Field(..., description="ID del propietario")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")


class VehicleWithOwner(VehicleResponse):
    """Schema for vehicle response with owner details."""
    owner_name: str = Field(..., description="Nombre del propietario")
    owner_email: str = Field(..., description="Email del propietario")


class VehicleListResponse(BaseModel):
    """Schema for paginated vehicle list response."""
    vehicles: list[VehicleResponse] = Field(..., description="Lista de vehículos")
    total: int = Field(..., description="Total de vehículos encontrados")
    page: int = Field(..., description="Número de página actual")
    page_size: int = Field(..., description="Cantidad de resultados por página")
