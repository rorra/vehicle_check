"""
Script to automatically create annual inspections for eligible vehicles.

This script should be run periodically (e.g., daily via cron).

Logic:
- January-October: Creates inspections for vehicles whose last PASSED inspection
  was approved 11+ months ago
- November-December: Creates inspections for ALL vehicles from last year that
  don't have one for current year yet (catch-all)

This ensures vehicles get their annual inspection every year without exception.

Usage:
    python script/create_annual_inspections.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models import AnnualInspection, AnnualStatus, generate_uuid


def create_annual_inspections_for_eligible_vehicles(session: Session) -> int:
    """
    Create annual inspections for vehicles that are eligible.

    Eligibility depends on current month:
    - Jan-Oct: PASSED inspections from last year approved 11+ months ago
    - Nov-Dec: ALL PASSED inspections from last year without current year inspection

    Args:
        session: Database session

    Returns:
        Number of annual inspections created
    """
    current_date = datetime.now()
    current_year = current_date.year
    last_year = current_year - 1
    current_month = current_date.month

    if current_month >= 11:
        # November-December: Create for ALL vehicles from last year
        print(f"Modo noviembre-diciembre: creando inspecciones para todos los vehículos de {last_year}")

        passed_inspections = session.query(AnnualInspection).filter(
            AnnualInspection.year == last_year,
            AnnualInspection.status == AnnualStatus.PASSED
        ).all()
    else:
        # January-October: Create only for those approved 11+ months ago
        cutoff_date = current_date - timedelta(days=11 * 30)  # Approximately 11 months
        print(f"Modo enero-octubre: creando inspecciones aprobadas antes del {cutoff_date.strftime('%Y-%m-%d')}")

        passed_inspections = session.query(AnnualInspection).filter(
            AnnualInspection.year == last_year,
            AnnualInspection.status == AnnualStatus.PASSED,
            AnnualInspection.updated_at <= cutoff_date
        ).all()

    if not passed_inspections:
        print("\nNo se encontraron inspecciones del año pasado.")
        return 0

    # Get all vehicle IDs from passed inspections
    vehicle_ids = [insp.vehicle_id for insp in passed_inspections]

    # Bulk query: Get all existing inspections for current year for these vehicles
    existing_inspections = session.query(AnnualInspection.vehicle_id).filter(
        AnnualInspection.year == current_year,
        AnnualInspection.vehicle_id.in_(vehicle_ids)
    ).all()

    # Create set of vehicle IDs that already have current year inspection
    existing_vehicle_ids = {insp.vehicle_id for insp in existing_inspections}

    print(f"Vehículos con inspección de {last_year}: {len(passed_inspections)}")
    print(f"Vehículos que ya tienen inspección de {current_year}: {len(existing_vehicle_ids)}")

    # Create inspections for vehicles that don't have one for current year
    new_inspections = []
    for inspection in passed_inspections:
        if inspection.vehicle_id not in existing_vehicle_ids:
            new_inspection = AnnualInspection(
                id=generate_uuid(),
                vehicle_id=inspection.vehicle_id,
                year=current_year,
                status=AnnualStatus.PENDING,
                attempt_count=0,
            )
            new_inspections.append(new_inspection)

    if new_inspections:
        # Bulk insert
        session.bulk_save_objects(new_inspections)
        session.commit()
        print(f"\nTotal de inspecciones anuales creadas: {len(new_inspections)}")
    else:
        print("\nNo se encontraron vehículos elegibles para crear inspecciones anuales.")

    return len(new_inspections)


def main():
    """Main entry point for the script."""
    print("Iniciando script de creación automática de inspecciones anuales...")
    print(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Create database session
    session = SessionLocal()

    try:
        created_count = create_annual_inspections_for_eligible_vehicles(session)
        print("\nScript completado exitosamente.")
        return 0

    except Exception as e:
        print(f"\nError al ejecutar el script: {str(e)}")
        session.rollback()
        return 1

    finally:
        session.close()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
