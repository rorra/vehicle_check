from typing import Optional
from fastapi import APIRouter, Depends, status, Query, Path
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models import User
from app.schemas.vehicle import (
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse,
    VehicleWithOwner,
    VehicleListResponse,
)
from app.services.vehicle_service import VehicleService

router = APIRouter()


@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    vehicle_data: VehicleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new vehicle.

    - CLIENT: Can only create vehicles for themselves
    - ADMIN: Can create vehicles for any user by specifying owner_id
    """
    service = VehicleService(db)
    return service.create(
        current_user,
        vehicle_data.plate_number,
        vehicle_data.make,
        vehicle_data.model,
        vehicle_data.year,
        vehicle_data.owner_id
    )


@router.get("/", response_model=VehicleListResponse)
def list_vehicles(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Cantidad de resultados por página"),
    search: Optional[str] = Query(None, description="Buscar por matrícula, marca o modelo"),
    owner_id: Optional[str] = Query(None, description="Filtrar por propietario (solo ADMIN)"),
    include_inactive: bool = Query(False, description="Incluir vehículos deshabilitados"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List vehicles with pagination.

    - CLIENT: Can only see their own active vehicles (disabled vehicles are hidden)
    - ADMIN: Can see all vehicles, with optional filtering by owner and status
    - INSPECTOR: Cannot list vehicles
    """
    service = VehicleService(db)
    vehicles, total = service.list(current_user, page, page_size, search, owner_id, include_inactive)

    return VehicleListResponse(
        vehicles=vehicles,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/with-owners", response_model=list[VehicleWithOwner])
def list_vehicles_with_owners(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all vehicles with owner details.

    Only accessible by ADMIN.
    """
    service = VehicleService(db)
    vehicles = service.list_with_owners()

    result = []
    for vehicle in vehicles:
        result.append({
            "id": vehicle.id,
            "plate_number": vehicle.plate_number,
            "make": vehicle.make,
            "model": vehicle.model,
            "year": vehicle.year,
            "owner_id": vehicle.owner_id,
            "is_active": vehicle.is_active,
            "created_at": vehicle.created_at,
            "updated_at": vehicle.updated_at,
            "owner_name": vehicle.owner.name,
            "owner_email": vehicle.owner.email,
        })

    return result


@router.get("/plate/{plate_number}", response_model=VehicleResponse)
def get_vehicle_by_plate(
    plate_number: str = Path(..., description="Número de matrícula del vehículo", examples=["ABC123"]),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get vehicle by plate number.

    - CLIENT: Can only access their own vehicles
    - ADMIN: Can access any vehicle
    - INSPECTOR: Can access any vehicle (needed for inspections)
    """
    service = VehicleService(db)
    return service.get_by_plate(plate_number, current_user)


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: str = Path(..., description="ID único del vehículo"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get vehicle details by ID.

    - CLIENT: Can only access their own vehicles
    - ADMIN: Can access any vehicle
    - INSPECTOR: Can access any vehicle (needed for inspections)
    """
    service = VehicleService(db)
    return service.get(vehicle_id, current_user)


@router.put("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: str = Path(..., description="ID único del vehículo a actualizar"),
    vehicle_data: VehicleUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update vehicle details.

    - CLIENT: Can only update their own vehicles
    - ADMIN: Can update any vehicle
    - INSPECTOR: Cannot update vehicles
    """
    service = VehicleService(db)
    return service.update(
        vehicle_id,
        current_user,
        vehicle_data.plate_number,
        vehicle_data.make,
        vehicle_data.model,
        vehicle_data.year
    )


@router.delete("/{vehicle_id}", status_code=status.HTTP_200_OK)
def delete_vehicle(
    vehicle_id: str = Path(..., description="ID único del vehículo a eliminar"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a vehicle.

    - CLIENT: Can only delete their own vehicles (if no inspections exist)
    - ADMIN: Can delete any vehicle (with cascade to inspections)
    - INSPECTOR: Cannot delete vehicles
    """
    service = VehicleService(db)
    service.delete(vehicle_id, current_user)
    return {"message": "Vehículo eliminado exitosamente"}
