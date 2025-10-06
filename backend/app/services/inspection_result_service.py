from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import (
    InspectionResult,
    ItemCheck,
    CheckItemTemplate,
    AnnualInspection,
    Appointment,
    Inspector,
    User,
    UserRole,
    Vehicle,
)


class InspectionResultService:
    """Service layer for inspection result business logic."""

    def __init__(self, db: Session):
        self.db = db

    def list(
        self,
        current_user: User,
        page: int,
        page_size: int,
        year: Optional[int] = None,
        vehicle_id: Optional[str] = None,
        passed_only: Optional[bool] = None
    ) -> Tuple[List[InspectionResult], int]:
        """
        List inspection results with pagination and filters.

        Args:
            current_user: The requesting user
            page: Page number
            page_size: Results per page
            year: Filter by year (optional)
            vehicle_id: Filter by vehicle (optional)
            passed_only: Filter by pass/fail status (optional)

        Returns:
            Tuple of (results list, total count)
        """
        # Build base query
        query = self.db.query(InspectionResult).join(
            AnnualInspection, InspectionResult.annual_inspection_id == AnnualInspection.id
        ).join(
            Appointment, InspectionResult.appointment_id == Appointment.id
        )

        # Apply role-based filtering
        if current_user.role == UserRole.CLIENT:
            query = query.join(Vehicle, AnnualInspection.vehicle_id == Vehicle.id).filter(
                Vehicle.owner_id == current_user.id
            )

        # Apply additional filters
        if year:
            query = query.filter(AnnualInspection.year == year)
        if vehicle_id:
            query = query.filter(AnnualInspection.vehicle_id == vehicle_id)
        if passed_only is not None:
            if passed_only:
                query = query.filter(InspectionResult.total_score >= 40)
            else:
                query = query.filter(InspectionResult.total_score < 40)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        results = query.order_by(InspectionResult.created_at.desc()).offset(offset).limit(page_size).all()

        return results, total

    def get(self, result_id: str, current_user: User) -> InspectionResult:
        """
        Get detailed inspection result by ID.

        Args:
            result_id: The result ID
            current_user: The requesting user

        Returns:
            The inspection result

        Raises:
            HTTPException: If result not found or access denied
        """
        result = self.db.query(InspectionResult).filter(
            InspectionResult.id == result_id
        ).first()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resultado de inspección no encontrado"
            )

        # Check access permissions for clients
        if current_user.role == UserRole.CLIENT:
            if result.annual_inspection.vehicle.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para ver este resultado"
                )

        return result

    def get_item_checks(self, result_id: str) -> List[ItemCheck]:
        """
        Get all item checks for a result, ordered by template ordinal.

        Args:
            result_id: The result ID

        Returns:
            List of item checks
        """
        return self.db.query(ItemCheck).join(CheckItemTemplate).filter(
            ItemCheck.inspection_result_id == result_id
        ).order_by(CheckItemTemplate.ordinal).all()

    def get_inspector_name(self, appointment_id: str) -> Optional[str]:
        """
        Get inspector name from appointment.

        Args:
            appointment_id: The appointment ID

        Returns:
            Inspector name or None
        """
        appointment = self.db.query(Appointment).filter(
            Appointment.id == appointment_id
        ).first()

        if not appointment or not appointment.inspector_id:
            return None

        inspector = self.db.query(Inspector).join(User).filter(
            Inspector.id == appointment.inspector_id
        ).first()

        return inspector.user.name if inspector else None

    def get_by_annual_inspection(
        self,
        annual_inspection_id: str,
        current_user: User
    ) -> List[InspectionResult]:
        """
        Get all inspection results for a specific annual inspection.

        Args:
            annual_inspection_id: The annual inspection ID
            current_user: The requesting user

        Returns:
            List of inspection results

        Raises:
            HTTPException: If annual inspection not found or access denied
        """
        # Get annual inspection
        annual = self.db.query(AnnualInspection).filter(
            AnnualInspection.id == annual_inspection_id
        ).first()

        if not annual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inspección anual no encontrada"
            )

        # Check access permissions for clients
        if current_user.role == UserRole.CLIENT:
            if annual.vehicle.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No tienes permisos para ver estos resultados"
                )

        # Get all results for this annual inspection
        results = self.db.query(InspectionResult).filter(
            InspectionResult.annual_inspection_id == annual_inspection_id
        ).order_by(InspectionResult.created_at.desc()).all()

        return results
