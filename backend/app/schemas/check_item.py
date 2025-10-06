from pydantic import BaseModel, field_validator, ConfigDict, Field
from typing import Optional
from datetime import datetime


class CheckItemTemplateCreate(BaseModel):
    """Schema for creating a new check item template."""
    code: str = Field(
        ...,
        description="Código único del ítem de chequeo",
        max_length=10,
        examples=["BRK", "LGT", "TIR"]
    )
    description: str = Field(
        ...,
        description="Descripción del ítem de chequeo",
        max_length=200,
        examples=["Frenos", "Luces e indicadores", "Neumáticos"]
    )
    ordinal: int = Field(
        ...,
        description="Orden de presentación (1-8)",
        ge=1,
        le=8,
        examples=[1, 2, 3]
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("El código no puede estar vacío")
        return v.strip().upper()


class CheckItemTemplateUpdate(BaseModel):
    """Schema for updating a check item template."""
    code: Optional[str] = Field(
        None,
        description="Nuevo código",
        max_length=10,
        examples=["BRK"]
    )
    description: Optional[str] = Field(
        None,
        description="Nueva descripción",
        max_length=200,
        examples=["Frenos"]
    )
    ordinal: Optional[int] = Field(
        None,
        description="Nuevo orden (1-8)",
        ge=1,
        le=8,
        examples=[1]
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if len(v.strip()) == 0:
                raise ValueError("El código no puede estar vacío")
            return v.strip().upper()
        return v


class CheckItemTemplateResponse(BaseModel):
    """Schema for check item template response."""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID único de la plantilla")
    code: str = Field(..., description="Código único")
    description: str = Field(..., description="Descripción")
    ordinal: int = Field(..., description="Orden de presentación")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de última actualización")
