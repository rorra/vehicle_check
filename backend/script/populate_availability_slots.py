"""
Script to populate availability slots for the next 30 days (Monday to Friday).
Creates slots from 8 AM to 2 PM, excluding weekends.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models import AvailabilitySlot, generate_uuid


def populate_slots(days: int = 30):
    """
    Create availability slots from 8 AM to 2 PM for the next N days, excluding weekends.

    Args:
        days: Number of days to create slots for (default: 30)
    """
    session = SessionLocal()
    slots_created = 0
    slots_skipped = 0

    try:
        now = datetime.now()
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)

            # Skip weekends (weekday() returns 5 for Saturday, 6 for Sunday)
            if current_date.weekday() in [5, 6]:
                print(f"Omitiendo final de semana: {current_date.strftime('%Y-%m-%d')}")
                continue

            # Create slots from 8 AM to 2 PM (each slot is 1 hour)
            for hour in range(8, 14):
                start = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                end = start + timedelta(hours=1)

                # Check if slot already exists
                existing = (
                    session.query(AvailabilitySlot)
                    .filter(
                        AvailabilitySlot.start_time == start,
                        AvailabilitySlot.end_time == end,
                    )
                    .one_or_none()
                )

                if existing:
                    slots_skipped += 1
                    continue

                # Create new slot
                slot = AvailabilitySlot(
                    id=generate_uuid(),
                    start_time=start,
                    end_time=end,
                    is_booked=False,
                )
                session.add(slot)
                slots_created += 1

        # Commit all changes
        session.commit()

        print(f"Proceso completado:")
        print(f"Slots creados: {slots_created}")
        print(f"Slots omitidos (ya existían): {slots_skipped}")
        print(f"Total slots procesados: {slots_created + slots_skipped}")

    except Exception as e:
        session.rollback()
        print(f"Error al crear slots: {str(e)}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Creando slots de disponibilidad")
    print("=" * 60)
    print(f"Fecha de inicio: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Días a procesar: 30")
    print(f"Horario: 8:00 AM - 2:00 PM")
    print(f"Días excluidos: Sábados y domingos")
    print("=" * 60)
    print()

    # Allow custom days parameter from command line
    days = 30
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
            print(f"Usando {days} días desde argumento de línea de comandos")
        except ValueError:
            print("Argumento inválido, usando 30 días por defecto")

    populate_slots(days=days)
