from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import Vehicle, User, UserRole, generate_uuid


class VehicleService:
    """Service layer for vehicle business logic."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        current_user: User,
        plate_number: str,
        make: str,
        model: str,
        year: int,
        owner_id: Optional[str] = None
    ) -> Vehicle:
        """
        Create a new vehicle.

        Args:
            current_user: The requesting user
            plate_number: Vehicle plate number
            make: Vehicle make
            model: Vehicle model
            year: Vehicle year
            owner_id: Owner ID (optional, for admins creating for other users)

        Returns:
            The created vehicle

        Raises:
            HTTPException: If validation fails
        """
        # Determine the owner
        if current_user.role == UserRole.ADMIN and owner_id:
            # Admin creating vehicle for specific user
            owner = self.db.query(User).filter(User.id == owner_id).first()
            if not owner:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Usuario propietario no encontrado"
                )
            final_owner_id = owner_id
        elif current_user.role == UserRole.CLIENT:
            # Client creating vehicle for themselves
            final_owner_id = current_user.id
        else:
            # Inspector cannot create vehicles
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los inspectores no pueden registrar vehículos"
            )

        # Check if plate number already exists
        existing_vehicle = self.db.query(Vehicle).filter(
            Vehicle.plate_number == plate_number
        ).first()

        if existing_vehicle:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un vehículo con esta matrícula"
            )

        # Create vehicle
        new_vehicle = Vehicle(
            id=generate_uuid(),
            plate_number=plate_number,
            make=make,
            model=model,
            year=year,
            owner_id=final_owner_id,
        )

        self.db.add(new_vehicle)
        self.db.commit()
        self.db.refresh(new_vehicle)

        return new_vehicle

    def list(
        self,
        current_user: User,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        owner_id: Optional[str] = None
    ) -> Tuple[List[Vehicle], int]:
        """
        List vehicles with pagination.

        Args:
            current_user: The requesting user
            page: Page number
            page_size: Results per page
            search: Search by plate, make, or model (optional)
            owner_id: Filter by owner (optional, admin only)

        Returns:
            Tuple of (vehicles list, total count)

        Raises:
            HTTPException: If inspector tries to list vehicles
        """
        if current_user.role == UserRole.INSPECTOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los inspectores no tienen acceso a la lista de vehículos"
            )

        # Build query
        query = self.db.query(Vehicle)

        # Filter by owner based on role
        if current_user.role == UserRole.CLIENT:
            query = query.filter(Vehicle.owner_id == current_user.id)
        elif current_user.role == UserRole.ADMIN and owner_id:
            query = query.filter(Vehicle.owner_id == owner_id)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Vehicle.plate_number.ilike(search_pattern),
                    Vehicle.make.ilike(search_pattern),
                    Vehicle.model.ilike(search_pattern),
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        vehicles = query.order_by(Vehicle.created_at.desc()).offset(offset).limit(page_size).all()

        return vehicles, total

    def list_with_owners(self) -> List[Vehicle]:
        """
        List all vehicles with owner details.

        Returns:
            List of vehicles
        """
        return self.db.query(Vehicle).join(User).all()

    def get_by_plate(self, plate_number: str, current_user: User) -> Vehicle:
        """
        Get vehicle by plate number.

        Args:
            plate_number: The plate number
            current_user: The requesting user

        Returns:
            The vehicle

        Raises:
            HTTPException: If vehicle not found or access denied
        """
        vehicle = self.db.query(Vehicle).filter(
            Vehicle.plate_number == plate_number.upper()
        ).first()

        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehículo no encontrado"
            )

        # Check access permissions
        if current_user.role == UserRole.CLIENT and vehicle.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver este vehículo"
            )

        return vehicle

    def get(self, vehicle_id: str, current_user: User) -> Vehicle:
        """
        Get vehicle details by ID.

        Args:
            vehicle_id: The vehicle ID
            current_user: The requesting user

        Returns:
            The vehicle

        Raises:
            HTTPException: If vehicle not found or access denied
        """
        vehicle = self.db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehículo no encontrado"
            )

        # Check access permissions
        if current_user.role == UserRole.CLIENT and vehicle.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para ver este vehículo"
            )

        return vehicle

    def update(
        self,
        vehicle_id: str,
        current_user: User,
        plate_number: Optional[str] = None,
        make: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None
    ) -> Vehicle:
        """
        Update vehicle details.

        Args:
            vehicle_id: The vehicle ID
            current_user: The requesting user
            plate_number: New plate number (optional)
            make: New make (optional)
            model: New model (optional)
            year: New year (optional)

        Returns:
            The updated vehicle

        Raises:
            HTTPException: If validation fails or access denied
        """
        if current_user.role == UserRole.INSPECTOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los inspectores no pueden modificar vehículos"
            )

        vehicle = self.db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehículo no encontrado"
            )

        # Check access permissions
        if current_user.role == UserRole.CLIENT and vehicle.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para modificar este vehículo"
            )

        # Check if new plate number already exists
        if plate_number and plate_number != vehicle.plate_number:
            existing = self.db.query(Vehicle).filter(
                Vehicle.plate_number == plate_number
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un vehículo con esta matrícula"
                )

        # Update fields
        if plate_number is not None:
            vehicle.plate_number = plate_number
        if make is not None:
            vehicle.make = make
        if model is not None:
            vehicle.model = model
        if year is not None:
            vehicle.year = year

        self.db.commit()
        self.db.refresh(vehicle)

        return vehicle

    def delete(self, vehicle_id: str, current_user: User) -> None:
        """
        Delete a vehicle.

        Args:
            vehicle_id: The vehicle ID
            current_user: The requesting user

        Raises:
            HTTPException: If validation fails or access denied
        """
        if current_user.role == UserRole.INSPECTOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Los inspectores no pueden eliminar vehículos"
            )

        vehicle = self.db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()

        if not vehicle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehículo no encontrado"
            )

        # Check access permissions
        if current_user.role == UserRole.CLIENT and vehicle.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para eliminar este vehículo"
            )

        # Check if vehicle has inspections
        if len(vehicle.annual_inspections) > 0:
            if current_user.role == UserRole.CLIENT:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No se puede eliminar un vehículo con inspecciones registradas"
                )
            # Admin can delete with cascade

        self.db.delete(vehicle)
        self.db.commit()
