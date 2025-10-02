from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, Field
from typing import Optional
from app.models import UserRole


class UserRegister(BaseModel):
    name: str = Field(
        ...,
        description="Nombre completo del usuario",
        min_length=2,
        examples=["Juan Pérez"]
    )
    email: EmailStr = Field(
        ...,
        description="Correo electrónico del usuario",
        examples=["juan@example.com"]
    )
    password: str = Field(
        ...,
        description="Contraseña del usuario (mínimo 6 caracteres)",
        min_length=6,
        examples=["password123"]
    )
    role: UserRole = Field(
        UserRole.CLIENT,
        description="Rol del usuario: CLIENT, INSPECTOR o ADMIN",
        examples=["CLIENT"]
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if len(v) < 2:
            raise ValueError("El nombre debe tener al menos 2 caracteres")
        return v


class UserLogin(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Correo electrónico del usuario",
        examples=["juan@example.com"]
    )
    password: str = Field(
        ...,
        description="Contraseña del usuario",
        examples=["password123"]
    )


class Token(BaseModel):
    access_token: str = Field(..., description="Token JWT de acceso")
    token_type: str = Field("bearer", description="Tipo de token")


class TokenData(BaseModel):
    user_id: Optional[str] = Field(None, description="ID del usuario")
    email: Optional[str] = Field(None, description="Email del usuario")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="ID único del usuario")
    name: str = Field(..., description="Nombre completo del usuario")
    email: str = Field(..., description="Correo electrónico")
    role: UserRole = Field(..., description="Rol del usuario")
    is_active: bool = Field(..., description="Si el usuario está activo")


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Correo electrónico del usuario",
        examples=["juan@example.com"]
    )


class ResetPasswordRequest(BaseModel):
    token: str = Field(
        ...,
        description="Token de restablecimiento de contraseña",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
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
