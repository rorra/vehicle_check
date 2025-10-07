from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models import AvailabilitySlot, generate_uuid
from app.schemas.appointment import AvailableSlotCreate


class AvailableSlotService:
    """Service layer for available slot business logic."""

    def __init__(self, db: Session):
        self.db = db

    def create(self, slot_data: AvailableSlotCreate) -> AvailabilitySlot:
        """
        Create a new availability slot.

        Args:
            slot_data: The slot creation data (only start_time required)

        Returns:
            The created slot

        Raises:
            HTTPException: If validation fails
        """
        # Automatically calculate end_time as start_time + 1 hour
        end_time = slot_data.start_time + timedelta(hours=1)

        # Check for overlapping slots
        overlapping = self.db.query(AvailabilitySlot).filter(
            AvailabilitySlot.start_time < end_time,
            AvailabilitySlot.end_time > slot_data.start_time
        ).first()

        if overlapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un slot que se superpone con este horario"
            )

        # Create slot
        new_slot = AvailabilitySlot(
            id=generate_uuid(),
            start_time=slot_data.start_time,
            end_time=end_time,
            is_booked=False,
        )

        self.db.add(new_slot)
        self.db.commit()
        self.db.refresh(new_slot)

        return new_slot

    def list(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        include_booked: bool = False
    ) -> List[AvailabilitySlot]:
        """
        List availability slots with optional filters.

        Args:
            from_date: Filter slots from this date
            to_date: Filter slots until this date
            include_booked: Whether to include booked slots

        Returns:
            List of slots
        """
        query = self.db.query(AvailabilitySlot)

        if not include_booked:
            query = query.filter(AvailabilitySlot.is_booked == False)

        if from_date:
            query = query.filter(AvailabilitySlot.start_time >= from_date)
        if to_date:
            query = query.filter(AvailabilitySlot.end_time <= to_date)

        # Only show future slots by default
        if not from_date:
            query = query.filter(AvailabilitySlot.start_time > datetime.now(timezone.utc))

        slots = query.order_by(AvailabilitySlot.start_time.asc()).all()

        return slots

    def get(self, slot_id: str) -> AvailabilitySlot:
        """
        Get slot by ID.

        Args:
            slot_id: The slot ID

        Returns:
            The slot

        Raises:
            HTTPException: If slot not found
        """
        slot = self.db.query(AvailabilitySlot).filter(AvailabilitySlot.id == slot_id).first()
        if not slot:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot no encontrado"
            )
        return slot

    def delete(self, slot_id: str) -> None:
        """
        Delete a slot.

        Args:
            slot_id: The slot ID

        Raises:
            HTTPException: If slot not found or is already booked
        """
        slot = self.get(slot_id)

        # Cannot delete booked slots
        if slot.is_booked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede eliminar un slot que ya está reservado"
            )

        self.db.delete(slot)
        self.db.commit()

    def mark_as_booked(self, slot_id: str) -> AvailabilitySlot:
        """
        Mark a slot as booked.

        Args:
            slot_id: The slot ID

        Returns:
            The updated slot

        Raises:
            HTTPException: If slot not found or already booked
        """
        slot = self.get(slot_id)

        if slot.is_booked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este slot ya está reservado"
            )

        slot.is_booked = True
        self.db.commit()
        self.db.refresh(slot)

        return slot
