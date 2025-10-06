from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import (
    AnnualInspection,
    Vehicle,
    User,
    UserRole,
    AnnualStatus,
    Appointment,
    generate_uuid,
)
from app.schemas.annual_inspection import (
    AnnualInspectionCreate,
    AnnualInspectionUpdate,
)


class AnnualInspectionService:
    """Service layer for annual inspection business logic."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        inspection_data: AnnualInspectionCreate,
        current_user: User
    ) -> AnnualInspection:
        """
        Create a new annual inspection.

        Args:
            inspection_data: The inspection creation data
            current_user: The current authenticated user

        Returns:
            The created annual inspection

        Raises:
            HTTPException: If validation fails or operation is not permitted
        """
        # Validate user role
        if current_user.role == UserRole.INSPECTOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los inspectores no pueden crear inspecciones anuales"
            )

        # Verify vehicle exists
        vehicle = self._get_vehicle(inspection_data.vehicle_id)

        # Check ownership for clients
        if current_user.role == UserRole.CLIENT and vehicle.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para crear inspecciones para este vehículo"
            )

        # Check if annual inspection already exists for this vehicle and year
        existing = self.db.query(AnnualInspection).filter(
            AnnualInspection.vehicle_id == inspection_data.vehicle_id,
            AnnualInspection.year == inspection_data.year
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una inspección anual para este vehículo en el año especificado"
            )

        # Create annual inspection
        new_inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=inspection_data.vehicle_id,
            year=inspection_data.year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )

        self.db.add(new_inspection)
        self.db.commit()
        self.db.refresh(new_inspection)

        return new_inspection

    def list(
        self,
        current_user: User,
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[AnnualStatus] = None,
        year: Optional[int] = None,
        vehicle_id: Optional[str] = None
    ) -> Tuple[List[AnnualInspection], int]:
        """
        List annual inspections with pagination and filters.

        Args:
            current_user: The current authenticated user
            page: Page number (1-indexed)
            page_size: Number of results per page
            status_filter: Filter by inspection status
            year: Filter by year
            vehicle_id: Filter by vehicle ID

        Returns:
            Tuple of (list of annual inspections, total count)
        """
        # Build base query
        query = self.db.query(AnnualInspection).join(
            Vehicle, AnnualInspection.vehicle_id == Vehicle.id
        ).join(User, Vehicle.owner_id == User.id)

        # Apply role-based filtering
        if current_user.role == UserRole.CLIENT:
            query = query.filter(Vehicle.owner_id == current_user.id)

        # Apply additional filters
        if status_filter:
            query = query.filter(AnnualInspection.status == status_filter)
        if year:
            query = query.filter(AnnualInspection.year == year)
        if vehicle_id:
            query = query.filter(AnnualInspection.vehicle_id == vehicle_id)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        inspections = query.order_by(AnnualInspection.created_at.desc()).offset(offset).limit(page_size).all()

        return inspections, total

    def get(self, inspection_id: str, current_user: User) -> AnnualInspection:
        """
        Get annual inspection details by ID.

        Args:
            inspection_id: The ID of the annual inspection
            current_user: The current authenticated user

        Returns:
            The annual inspection

        Raises:
            HTTPException: If inspection not found or user doesn't have permission
        """
        inspection = self._get_inspection(inspection_id)

        # Check access permissions for clients
        if current_user.role == UserRole.CLIENT:
            if inspection.vehicle.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para ver esta inspección"
                )

        return inspection

    def update(
        self,
        inspection_id: str,
        inspection_data: AnnualInspectionUpdate,
        current_user: User
    ) -> AnnualInspection:
        """
        Update annual inspection status.

        Args:
            inspection_id: The ID of the annual inspection to update
            inspection_data: The update data
            current_user: The current authenticated user (must be admin)

        Returns:
            The updated annual inspection

        Raises:
            HTTPException: If inspection not found or user is not admin
        """
        # This endpoint is admin-only, validation happens in the route via require_admin
        inspection = self._get_inspection(inspection_id)

        # Update fields
        if inspection_data.status is not None:
            inspection.status = inspection_data.status

        self.db.commit()
        self.db.refresh(inspection)

        return inspection

    def delete(self, inspection_id: str, current_user: User) -> None:
        """
        Delete an annual inspection.

        Args:
            inspection_id: The ID of the annual inspection to delete
            current_user: The current authenticated user (must be admin)

        Raises:
            HTTPException: If inspection not found or user is not admin
        """
        # This endpoint is admin-only, validation happens in the route via require_admin
        inspection = self._get_inspection(inspection_id)

        self.db.delete(inspection)
        self.db.commit()

    def get_appointment_statistics(self, inspection_id: str) -> dict:
        """
        Get appointment statistics for an annual inspection.

        Args:
            inspection_id: The ID of the annual inspection

        Returns:
            Dictionary with appointment count and last appointment date
        """
        appointment_count = self.db.query(func.count(Appointment.id)).filter(
            Appointment.annual_inspection_id == inspection_id
        ).scalar()

        last_appointment = self.db.query(Appointment).filter(
            Appointment.annual_inspection_id == inspection_id
        ).order_by(Appointment.date_time.desc()).first()

        return {
            "total_appointments": appointment_count,
            "last_appointment_date": last_appointment.date_time if last_appointment else None
        }

    # Private helper methods

    def _get_vehicle(self, vehicle_id: str) -> Vehicle:
        """Get vehicle by ID."""
        vehicle = self.db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehículo no encontrado"
            )
        return vehicle

    def _get_inspection(self, inspection_id: str) -> AnnualInspection:
        """Get annual inspection by ID."""
        inspection = self.db.query(AnnualInspection).filter(
            AnnualInspection.id == inspection_id
        ).first()
        if not inspection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inspección anual no encontrada"
            )
        return inspection
