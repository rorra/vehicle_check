from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, security
from app.models import User, UserSession, generate_uuid
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    service = AuthService(db)
    return service.register_user(user_data)


@router.post("/login", response_model=Token)
def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token."""
    service = AuthService(db)
    access_token, user = service.login(user_credentials.email, user_credentials.password)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Request password reset token."""
    service = AuthService(db)
    service.request_password_reset(request.email)

    # Always return same message for security (don't reveal if email exists)
    return {
        "message": "Si el correo existe, recibirás un enlace para restablecer tu contraseña"
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using reset token."""
    service = AuthService(db)
    service.reset_password(request.token, request.new_password)
    return {"message": "Contraseña restablecida exitosamente"}


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout user by revoking the current session.
    Requires valid authentication token.
    """
    service = AuthService(db)
    service.logout(credentials.credentials, current_user.id)
    return {"message": "Sesión cerrada exitosamente"}
