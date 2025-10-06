from pydantic import BaseModel, field_validator, ConfigDict, Field
from typing import Optional
from datetime import datetime, timezone
from app.models import AppointmentStatus, CreatedChannel


class AppointmentCreate(BaseModel):
    """Schema for creating a new appointment."""
    vehicle_id: str = Field(
        ...,
        description="ID del vehículo a inspeccionar",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    annual_inspection_id: str = Field(
        ...,
        description="ID de la inspección anual",
        examples=["550e8400-e29b-41d4-a716-446655440001"]
    )
    date_time: datetime = Field(
        ...,
        description="Fecha y hora del turno",
        examples=["2024-03-15T10:00:00"]
    )
    inspector_id: Optional[str] = Field(
        None,
        description="ID del inspector asignado (solo ADMIN puede especificar)",
        examples=["550e8400-e29b-41d4-a716-446655440002"]
    )

    @field_validator("date_time")
    @classmethod
    def validate_future_date(cls, v: datetime) -> datetime:
        # Make comparison timezone-aware
        now = datetime.now(timezone.utc) if v.tzinfo else datetime.now()
        if v < now:
            raise ValueError("La fecha del turno debe ser futura")
        return v


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment."""
    date_time: Optional[datetime] = Field(
        None,
        description="Nueva fecha y hora del turno",
        examples=["2024-03-16T14:00:00"]
    )
    inspector_id: Optional[str] = Field(
        None,
        description="ID del nuevo inspector asignado",
        examples=["550e8400-e29b-41d4-a716-446655440002"]
    )
    status: Optional[AppointmentStatus] = Field(
        None,
        description="Nuevo estado del turno",
        examples=["CONFIRMED"]
    )

    @field_validator("date_time")
    @classmethod
    def validate_future_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v is not None:
            # Make comparison timezone-aware
            now = datetime.now(timezone.utc) if v.tzinfo else datetime.now()
            if v < now:
                raise ValueError("La fecha del turno debe ser futura")
        return v


class AppointmentResponse(BaseModel):
    """Schema for appointment response."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID único del turno")
    annual_inspection_id: str = Field(..., description="ID de la inspección anual")
    vehicle_id: str = Field(..., description="ID del vehículo")
    inspector_id: Optional[str] = Field(None, description="ID del inspector asignado")
    created_by_user_id: str = Field(..., description="ID del usuario que creó el turno")
    created_channel: CreatedChannel = Field(..., description="Canal por el que se creó el turno")
    date_time: datetime = Field(..., description="Fecha y hora del turno")
    status: AppointmentStatus = Field(..., description="Estado del turno")
    confirmation_token: Optional[str] = Field(None, description="Token de confirmación")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")


class AppointmentWithDetails(AppointmentResponse):
    """Schema for appointment response with related entity details."""
    vehicle_plate: str = Field(..., description="Matrícula del vehículo")
    vehicle_make: Optional[str] = Field(None, description="Marca del vehículo")
    vehicle_model: Optional[str] = Field(None, description="Modelo del vehículo")
    owner_name: str = Field(..., description="Nombre del propietario")
    owner_email: str = Field(..., description="Email del propietario")
    inspector_name: Optional[str] = Field(None, description="Nombre del inspector")


class AppointmentListResponse(BaseModel):
    """Schema for paginated appointment list response."""
    appointments: list[AppointmentWithDetails] = Field(..., description="Lista de turnos")
    total: int = Field(..., description="Total de turnos encontrados")
    page: int = Field(..., description="Número de página actual")
    page_size: int = Field(..., description="Cantidad de resultados por página")


class AvailableSlotResponse(BaseModel):
    """Schema for available time slot response."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID único del slot")
    start_time: datetime = Field(..., description="Hora de inicio")
    end_time: datetime = Field(..., description="Hora de fin")
    is_booked: bool = Field(..., description="Si el slot está reservado")


class CompleteAppointmentRequest(BaseModel):
    """Schema for completing an appointment with inspection result."""
    total_score: int = Field(
        ...,
        description="Puntaje total de la inspección (0-80)",
        ge=0,
        le=80,
        examples=[65]
    )
    item_scores: list[int] = Field(
        ...,
        description="Puntajes de los 8 ítems de chequeo (cada uno 0-10)",
        min_length=8,
        max_length=8,
        examples=[[8, 7, 9, 8, 7, 8, 9, 9]]
    )
    owner_observation: Optional[str] = Field(
        None,
        description="Observaciones del inspector",
        max_length=500,
        examples=["Vehículo en excelente condición"]
    )

    @field_validator("item_scores")
    @classmethod
    def validate_item_scores(cls, v: list[int]) -> list[int]:
        if len(v) != 8:
            raise ValueError("Se requieren exactamente 8 puntajes de ítems")
        for score in v:
            if score < 0 or score > 10:
                raise ValueError("Cada puntaje debe estar entre 0 y 10")
        if sum(v) > 80:
            raise ValueError("La suma de los puntajes no puede exceder 80")
        return v

    @field_validator("total_score")
    @classmethod
    def validate_total_score(cls, v: int) -> int:
        if v < 0 or v > 80:
            raise ValueError("El puntaje total debe estar entre 0 y 80")
        return v
