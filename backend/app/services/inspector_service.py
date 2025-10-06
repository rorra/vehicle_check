from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import Inspector, User, UserRole, generate_uuid


class InspectorService:
    """Service layer for inspector business logic."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, user_id: str, employee_id: str) -> Inspector:
        """
        Create a new inspector profile.

        Args:
            user_id: The user ID
            employee_id: The employee ID (will be uppercased)

        Returns:
            The created inspector

        Raises:
            HTTPException: If validation fails
        """
        # Verify user exists and is an inspector
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        if user.role != UserRole.INSPECTOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario debe tener rol INSPECTOR"
            )

        # Check if user already has an inspector profile
        existing = self.db.query(Inspector).filter(Inspector.user_id == user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El usuario ya tiene un perfil de inspector"
            )

        # Check if employee_id already exists
        existing_employee = self.db.query(Inspector).filter(
            Inspector.employee_id == employee_id.upper()
        ).first()
        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un inspector con este ID de empleado"
            )

        # Create inspector
        new_inspector = Inspector(
            id=generate_uuid(),
            user_id=user_id,
            employee_id=employee_id.upper(),
            active=True,
        )

        self.db.add(new_inspector)
        self.db.commit()
        self.db.refresh(new_inspector)

        return new_inspector

    def list(
        self,
        page: int,
        page_size: int,
        active_only: Optional[bool] = None
    ) -> Tuple[List[Inspector], int]:
        """
        List all inspectors with pagination.

        Args:
            page: Page number
            page_size: Results per page
            active_only: Filter by active status (optional)

        Returns:
            Tuple of (inspectors list, total count)
        """
        # Build query
        query = self.db.query(Inspector).join(User)

        # Filter by active status
        if active_only is not None:
            query = query.filter(Inspector.active == active_only)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        inspectors = query.order_by(Inspector.created_at.desc()).offset(offset).limit(page_size).all()

        return inspectors, total

    def get(self, inspector_id: str) -> Inspector:
        """
        Get inspector details by ID.

        Args:
            inspector_id: The inspector ID

        Returns:
            The inspector

        Raises:
            HTTPException: If inspector not found
        """
        inspector = self.db.query(Inspector).filter(Inspector.id == inspector_id).first()

        if not inspector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inspector no encontrado"
            )

        return inspector

    def update(
        self,
        inspector_id: str,
        employee_id: Optional[str] = None,
        active: Optional[bool] = None
    ) -> Inspector:
        """
        Update inspector details.

        Args:
            inspector_id: The inspector ID
            employee_id: New employee ID (optional)
            active: New active status (optional)

        Returns:
            The updated inspector

        Raises:
            HTTPException: If inspector not found or conflicts exist
        """
        inspector = self.db.query(Inspector).filter(Inspector.id == inspector_id).first()

        if not inspector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inspector no encontrado"
            )

        # Check if new employee_id already exists
        if employee_id and employee_id.upper() != inspector.employee_id:
            existing = self.db.query(Inspector).filter(
                Inspector.employee_id == employee_id.upper()
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un inspector con este ID de empleado"
                )

        # Update fields
        if employee_id is not None:
            inspector.employee_id = employee_id.upper()
        if active is not None:
            inspector.active = active

        self.db.commit()
        self.db.refresh(inspector)

        return inspector

    def delete(self, inspector_id: str) -> None:
        """
        Delete an inspector profile.

        Args:
            inspector_id: The inspector ID

        Raises:
            HTTPException: If inspector not found
        """
        inspector = self.db.query(Inspector).filter(Inspector.id == inspector_id).first()

        if not inspector:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inspector no encontrado"
            )

        self.db.delete(inspector)
        self.db.commit()
