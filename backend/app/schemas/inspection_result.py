from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime


class ItemCheckDetail(BaseModel):
    """Schema for individual item check in result."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID único del chequeo")
    check_item_template_id: str = Field(..., description="ID de la plantilla de chequeo")
    template_code: str = Field(..., description="Código de la plantilla")
    template_description: str = Field(..., description="Descripción de la plantilla")
    template_ordinal: int = Field(..., description="Orden de la plantilla")
    score: int = Field(..., description="Puntaje (0-10)")
    observation: Optional[str] = Field(None, description="Observaciones")


class InspectionResultDetail(BaseModel):
    """Schema for detailed inspection result."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID único del resultado")
    annual_inspection_id: str = Field(..., description="ID de la inspección anual")
    appointment_id: str = Field(..., description="ID del turno")
    total_score: int = Field(..., description="Puntaje total (0-80)")
    owner_observation: Optional[str] = Field(None, description="Observaciones generales")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")
    item_checks: list[ItemCheckDetail] = Field(..., description="Detalles de los 8 ítems chequeados")

    # Additional info
    vehicle_plate: str = Field(..., description="Matrícula del vehículo")
    vehicle_make: Optional[str] = Field(None, description="Marca del vehículo")
    vehicle_model: Optional[str] = Field(None, description="Modelo del vehículo")
    inspector_name: Optional[str] = Field(None, description="Nombre del inspector")
    inspection_date: datetime = Field(..., description="Fecha de la inspección")
    passed: bool = Field(..., description="Si la inspección fue aprobada")


class InspectionResultListItem(BaseModel):
    """Schema for inspection result in list."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID único del resultado")
    annual_inspection_id: str = Field(..., description="ID de la inspección anual")
    total_score: int = Field(..., description="Puntaje total")
    created_at: datetime = Field(..., description="Fecha de creación")
    vehicle_plate: str = Field(..., description="Matrícula del vehículo")
    year: int = Field(..., description="Año de la inspección")
    passed: bool = Field(..., description="Si fue aprobada")


class InspectionResultListResponse(BaseModel):
    """Schema for paginated inspection result list."""
    results: list[InspectionResultListItem] = Field(..., description="Lista de resultados")
    total: int = Field(..., description="Total de resultados encontrados")
    page: int = Field(..., description="Número de página actual")
    page_size: int = Field(..., description="Cantidad de resultados por página")
