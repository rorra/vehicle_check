from typing import List, Optional, Tuple
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models import Vehicle, User, UserRole, AnnualInspection, AnnualStatus, generate_uuid


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
            # If vehicle exists and is disabled, reassign it to new owner and enable it
            if not existing_vehicle.is_active:
                existing_vehicle.owner_id = final_owner_id
                existing_vehicle.is_active = True
                existing_vehicle.make = make
                existing_vehicle.model = model
                existing_vehicle.year = year

                # Create annual inspection for current year if doesn't exist
                current_year = datetime.now().year
                existing_annual = self.db.query(AnnualInspection).filter(
                    AnnualInspection.vehicle_id == existing_vehicle.id,
                    AnnualInspection.year == current_year
                ).first()

                if not existing_annual:
                    annual_inspection = AnnualInspection(
                        id=generate_uuid(),
                        vehicle_id=existing_vehicle.id,
                        year=current_year,
                        status=AnnualStatus.PENDING,
                        attempt_count=0,
                    )
                    self.db.add(annual_inspection)

                self.db.commit()
                self.db.refresh(existing_vehicle)
                return existing_vehicle
            else:
                # Vehicle exists and is active
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un vehículo activo con esta matrícula"
                )

        # Create new vehicle
        new_vehicle = Vehicle(
            id=generate_uuid(),
            plate_number=plate_number,
            make=make,
            model=model,
            year=year,
            owner_id=final_owner_id,
            is_active=True,
        )

        self.db.add(new_vehicle)
        self.db.flush()  # Flush to get the vehicle ID for the annual inspection

        # Automatically create annual inspection for current year
        current_year = datetime.now().year
        annual_inspection = AnnualInspection(
            id=generate_uuid(),
            vehicle_id=new_vehicle.id,
            year=current_year,
            status=AnnualStatus.PENDING,
            attempt_count=0,
        )
        self.db.add(annual_inspection)

        self.db.commit()
        self.db.refresh(new_vehicle)

        return new_vehicle

    def list(
        self,
        current_user: User,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        owner_id: Optional[str] = None,
        include_inactive: bool = False
    ) -> Tuple[List[Vehicle], int]:
        """
        List vehicles with pagination.

        Args:
            current_user: The requesting user
            page: Page number
            page_size: Results per page
            search: Search by plate, make, or model (optional)
            owner_id: Filter by owner (optional, admin only)
            include_inactive: Include disabled vehicles (default False, admin can override)

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
            # Clients only see active vehicles by default
            if not include_inactive:
                query = query.filter(Vehicle.is_active == True)
        elif current_user.role == UserRole.ADMIN:
            if owner_id:
                query = query.filter(Vehicle.owner_id == owner_id)
            # Admin can choose to include inactive vehicles
            if not include_inactive:
                query = query.filter(Vehicle.is_active == True)

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
        - CLIENT: Disables the vehicle (soft delete) to preserve records
        - ADMIN: Can permanently delete with cascade

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

        # CLIENT: Soft delete (disable) to preserve records
        if current_user.role == UserRole.CLIENT:
            vehicle.is_active = False
            self.db.commit()
        else:
            # ADMIN: Hard delete with cascade
            self.db.delete(vehicle)
            self.db.commit()
