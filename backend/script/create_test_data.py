"""
Populate the database with default demo data tied to the current date.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine, SessionLocal, Base
from app.core.security import get_password_hash
from app.models import *


def get_or_create_user(session: Session, *, email: str, defaults: dict) -> type[User] | User:
    u = session.query(User).filter(User.email == email).one_or_none()
    if u:
        return u
    u = User(id=generate_uuid(), email=email, **defaults)
    session.add(u)
    session.commit()
    print(f"Usuario obtenido: {u.name} ({u.email})")
    return u


def get_or_create_inspector(session: Session, *, user: User, employee_id: str) -> type[Inspector] | Inspector:
    ins = session.query(Inspector).filter(Inspector.user_id == user.id).one_or_none()
    if ins:
        return ins
    ins = Inspector(id=generate_uuid(), user_id=user.id, employee_id=employee_id, active=True)
    session.add(ins)
    session.commit()
    print(f"Inspector obtenido: {user.name} (legajo {employee_id})")
    return ins


def get_or_create_vehicle(session: Session, *, plate: str, owner: User, make: str, model: str, year: int) -> Vehicle:
    v = session.query(Vehicle).filter(Vehicle.plate_number == plate).one_or_none()
    if v:
        return v
    v = Vehicle(
        id=generate_uuid(),
        plate_number=plate,
        make=make,
        model=model,
        year=year,
        owner_id=owner.id,
    )
    session.add(v)
    session.commit()
    print(f"Vehículo obtenido: {v.make} {v.model} ({v.plate_number})")
    return v


def get_or_create_annual(session: Session, *, vehicle: Vehicle, year: int) -> AnnualInspection:
    a = (
        session.query(AnnualInspection)
        .filter(AnnualInspection.vehicle_id == vehicle.id, AnnualInspection.year == year)
        .one_or_none()
    )
    if a:
        return a
    a = AnnualInspection(
        id=generate_uuid(),
        vehicle_id=vehicle.id,
        year=year,
        status=AnnualStatus.PENDING,
        attempt_count=0,
    )
    session.add(a)
    session.commit()
    print(f"Inspección anual obtenida: vehículo {vehicle.plate_number}, año {year}")
    return a


def ensure_templates(session: Session) -> list[CheckItemTemplate]:
    """Ensure the 8 fixed templates exist, returns them ordered by ordinal."""
    existing = session.query(CheckItemTemplate).order_by(CheckItemTemplate.ordinal.asc()).all()
    if len(existing) == 8:
        return existing

    # Spanish labels per requirement
    data = [
        ("BRK", "Frenos"),
        ("LGT", "Luces e indicadores"),
        ("TIR", "Neumáticos"),
        ("ENG", "Motor y fugas"),
        ("STE", "Dirección"),
        ("SUS", "Suspensión"),
        ("EMI", "Emisiones"),
        ("SAF", "Elementos de seguridad"),
    ]
    # Upsert-ish creation by code
    created_or_found = []
    for idx, (code, desc) in enumerate(data, start=1):
        tpl = session.query(CheckItemTemplate).filter(CheckItemTemplate.code == code).one_or_none()
        if not tpl:
            tpl = CheckItemTemplate(
                id=generate_uuid(),
                code=code,
                description=desc,
                ordinal=idx,
            )
            session.add(tpl)
            session.flush()
        created_or_found.append(tpl)
    session.commit()
    print("Plantillas de chequeo obtenidas (8 ítems)")
    # Return ordered by ordinal
    return sorted(created_or_found, key=lambda t: t.ordinal)


def get_or_create_slot_block(session: Session, *, days: int = 30) -> list[AvailabilitySlot]:
    """Create availability slots from 8 AM to 2 PM for the next N days, excluding weekends."""
    slots: list[AvailabilitySlot] = []
    now = datetime.now()
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)

        # Skip weekends (weekday() returns 5 for Saturday, 6 for Sunday)
        if current_date.weekday() in [5, 6]:
            continue

        # Create slots from 8 AM to 2 PM (each slot is 1 hour)
        for hour in range(8, 14):
            start = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)

            existing = (
                session.query(AvailabilitySlot)
                .filter(
                    AvailabilitySlot.start_time == start,
                    AvailabilitySlot.end_time == end,
                )
                .one_or_none()
            )

            if existing:
                slots.append(existing)
                continue

            slot = AvailabilitySlot(
                id=generate_uuid(),
                start_time=start,
                end_time=end,
                is_booked=False,
            )
            session.add(slot)
            session.flush()
            slots.append(slot)

    session.commit()
    print(f"Slots de disponibilidad creados: {len(slots)} slots para los próximos {days} días (excluyendo fines de semana)")
    return slots


def get_or_create_appointment(
    session: Session,
    *,
    annual: AnnualInspection,
    vehicle: Vehicle,
    inspector: Inspector | None,
    created_by: User,
    when: datetime,
) -> Appointment:
    ap = (
        session.query(Appointment)
        .filter(
            Appointment.annual_inspection_id == annual.id,
            Appointment.date_time == when,
        )
        .one_or_none()
    )
    if ap:
        return ap

    # Find and book the matching availability slot
    slot = (
        session.query(AvailabilitySlot)
        .filter(AvailabilitySlot.start_time == when)
        .one_or_none()
    )
    if slot:
        if slot.is_booked:
            print(f"ADVERTENCIA: El slot para {when.strftime('%Y-%m-%d %H:%M')} ya está reservado")
        else:
            slot.is_booked = True
            session.flush()

    ap = Appointment(
        id=generate_uuid(),
        annual_inspection_id=annual.id,
        vehicle_id=vehicle.id,
        inspector_id=inspector.id if inspector else None,
        created_by_user_id=created_by.id,
        created_channel=CreatedChannel.CLIENT_PORTAL if created_by.role == UserRole.CLIENT else CreatedChannel.ADMIN_PANEL,
        date_time=when,
        status=AppointmentStatus.CONFIRMED,
        confirmation_token="CONFIRM-DEMO",
    )
    session.add(ap)
    session.commit()
    print(f"Turno obtenido: {vehicle.plate_number} el {when.strftime('%Y-%m-%d %H:%M')}")
    return ap


def get_or_create_result_with_items(
    session: Session,
    *,
    annual: AnnualInspection,
    appointment: Appointment,
    templates: list[CheckItemTemplate],
    scores: list[int],
    owner_observation_if_low_total: str | None,
) -> InspectionResult:
    res = (
        session.query(InspectionResult)
        .filter(InspectionResult.appointment_id == appointment.id)
        .one_or_none()
    )
    if not res:
        total_score = sum(scores[:8])
        res = InspectionResult(
            id=generate_uuid(),
            annual_inspection_id=annual.id,
            appointment_id=appointment.id,
            total_score=total_score,
            owner_observation=owner_observation_if_low_total if total_score < 40 else None,
        )
        session.add(res)
        session.flush()

        # Create 8 ItemCheck (one per template)
        for tpl, score in zip(templates, scores[:8]):
            ic = ItemCheck(
                id=generate_uuid(),
                inspection_result_id=res.id,
                check_item_template_id=tpl.id,
                score=score,
                observation=(
                    "Chequeo realizado sin observaciones críticas" if score >= 5 else "Problema detectado"
                ),
            )
            session.add(ic)

        # Optionally mark annual current_result_id
        annual.current_result_id = res.id
        session.commit()
        print(f"Resultado de inspección obtenido (puntaje total: {res.total_score})")
    else:
        # Ensure it has the 8 items; if not, backfill
        existing_tpl_ids = {ic.check_item_template_id for ic in res.item_checks}
        for tpl, score in zip(templates, scores[:8]):
            if tpl.id in existing_tpl_ids:
                continue
            ic = ItemCheck(
                id=generate_uuid(),
                inspection_result_id=res.id,
                check_item_template_id=tpl.id,
                score=score,
                observation=(
                    "Chequeo realizado sin observaciones críticas" if score >= 5 else "Problema detectado"
                ),
            )
            session.add(ic)
        # Update total if needed
        expected_total = sum(scores[:8])
        if res.total_score != expected_total:
            res.total_score = expected_total
        session.commit()
        print(f"Resultado de inspección verificado (puntaje total: {res.total_score})")

    return res


def main():
    print("Creando datos de demostración...")

    session = SessionLocal()

    # Admin user
    admin = get_or_create_user(
        session,
        email="admin@vehiclecheck.com",
        defaults=dict(
            name="Administrador General",
            role=UserRole.ADMIN,
            password_hash=get_password_hash("password"),
            is_active=True,
        ),
    )

    # Three clients
    client1 = get_or_create_user(
        session,
        email="client1@gmail.com",
        defaults=dict(
            name="Juan Pérez",
            role=UserRole.CLIENT,
            password_hash=get_password_hash("password"),
            is_active=True,
        ),
    )

    client2 = get_or_create_user(
        session,
        email="client2@gmail.com",
        defaults=dict(
            name="María Gómez",
            role=UserRole.CLIENT,
            password_hash=get_password_hash("password"),
            is_active=True,
        ),
    )

    client3 = get_or_create_user(
        session,
        email="client3@gmail.com",
        defaults=dict(
            name="Carlos Rodríguez",
            role=UserRole.CLIENT,
            password_hash=get_password_hash("password"),
            is_active=True,
        ),
    )

    client4 = get_or_create_user(
        session,
        email="client4@gmail.com",
        defaults=dict(
            name="Laura Martínez",
            role=UserRole.CLIENT,
            password_hash=get_password_hash("password"),
            is_active=True,
        ),
    )

    # Two inspectors
    inspector_user1 = get_or_create_user(
        session,
        email="inspector1@vehiclecheck.com",
        defaults=dict(
            name="Roberto López",
            role=UserRole.INSPECTOR,
            password_hash=get_password_hash("password"),
            is_active=True,
        ),
    )
    inspector1 = get_or_create_inspector(session, user=inspector_user1, employee_id="INS-001")

    inspector_user2 = get_or_create_user(
        session,
        email="inspector2@vehiclecheck.com",
        defaults=dict(
            name="Ana Fernández",
            role=UserRole.INSPECTOR,
            password_hash=get_password_hash("password"),
            is_active=True,
        ),
    )
    inspector2 = get_or_create_inspector(session, user=inspector_user2, employee_id="INS-002")

    # Ensure the 8 templates exist
    templates = ensure_templates(session)

    # Availability slots for the next days
    slots = get_or_create_slot_block(session, days=30)

    # Date calculations
    now = datetime.now()
    this_year = now.year
    last_year = now.year - 1
    next_week = now + timedelta(days=7)
    last_week = now - timedelta(days=7)
    tomorrow = now + timedelta(days=1)

    # CLIENT 1: Failed and approved revision last year, approved revision this year
    vehicle1 = get_or_create_vehicle(
        session,
        plate="ABC123",
        owner=client1,
        make="Toyota",
        model="Corolla",
        year=2018,
    )

    # Last year annual inspection with 2 attempts
    annual1_last = get_or_create_annual(session, vehicle=vehicle1, year=last_year)
    annual1_last.attempt_count = 2

    # First attempt last year: FAILED
    ap1_last_failed_time = datetime(last_year, 3, 15, 10, 0, 0)
    ap1_last_failed = get_or_create_appointment(
        session,
        annual=annual1_last,
        vehicle=vehicle1,
        inspector=inspector1,
        created_by=client1,
        when=ap1_last_failed_time,
    )
    ap1_last_failed.status = AppointmentStatus.COMPLETED

    scores_failed = [3, 4, 4, 5, 3, 5, 4, 6]  # total 34 -> failed
    result1_failed = get_or_create_result_with_items(
        session,
        annual=annual1_last,
        appointment=ap1_last_failed,
        templates=templates,
        scores=scores_failed,
        owner_observation_if_low_total="Frenos y suspensión requieren reparación urgente.",
    )
    annual1_last.status = AnnualStatus.FAILED
    session.flush()

    # Second attempt last year: PASSED
    ap1_last_passed_time = datetime(last_year, 4, 10, 11, 0, 0)
    ap1_last_passed = get_or_create_appointment(
        session,
        annual=annual1_last,
        vehicle=vehicle1,
        inspector=inspector1,
        created_by=client1,
        when=ap1_last_passed_time,
    )
    ap1_last_passed.status = AppointmentStatus.COMPLETED

    scores_passed_last = [7, 8, 8, 7, 8, 7, 9, 6]  # total 60 -> passed
    result1_passed_last = get_or_create_result_with_items(
        session,
        annual=annual1_last,
        appointment=ap1_last_passed,
        templates=templates,
        scores=scores_passed_last,
        owner_observation_if_low_total="",
    )
    annual1_last.status = AnnualStatus.PASSED
    annual1_last.current_result_id = result1_passed_last.id

    # This year: PASSED
    annual1_this = get_or_create_annual(session, vehicle=vehicle1, year=this_year)
    annual1_this.attempt_count = 1

    ap1_this_time = datetime(this_year, 2, 20, 10, 0, 0)
    ap1_this = get_or_create_appointment(
        session,
        annual=annual1_this,
        vehicle=vehicle1,
        inspector=inspector2,
        created_by=client1,
        when=ap1_this_time,
    )
    ap1_this.status = AppointmentStatus.COMPLETED

    scores_passed_this = [9, 8, 8, 9, 7, 8, 9, 7]  # total 65 -> passed
    result1_this = get_or_create_result_with_items(
        session,
        annual=annual1_this,
        appointment=ap1_this,
        templates=templates,
        scores=scores_passed_this,
        owner_observation_if_low_total="",
    )
    annual1_this.status = AnnualStatus.PASSED
    annual1_this.current_result_id = result1_this.id

    # CLIENT 2: Approved last year, pending appointment next week
    vehicle2 = get_or_create_vehicle(
        session,
        plate="XYZ789",
        owner=client2,
        make="Honda",
        model="Civic",
        year=2020,
    )

    # Last year: PASSED
    annual2_last = get_or_create_annual(session, vehicle=vehicle2, year=last_year)
    annual2_last.attempt_count = 1

    ap2_last_time = datetime(last_year, 6, 15, 14, 0, 0)
    ap2_last = get_or_create_appointment(
        session,
        annual=annual2_last,
        vehicle=vehicle2,
        inspector=inspector2,
        created_by=client2,
        when=ap2_last_time,
    )
    ap2_last.status = AppointmentStatus.COMPLETED

    scores_client2_last = [8, 7, 9, 8, 7, 8, 7, 9]  # total 63 -> passed
    result2_last = get_or_create_result_with_items(
        session,
        annual=annual2_last,
        appointment=ap2_last,
        templates=templates,
        scores=scores_client2_last,
        owner_observation_if_low_total="",
    )
    annual2_last.status = AnnualStatus.PASSED
    annual2_last.current_result_id = result2_last.id

    # This year: Pending appointment for next week
    annual2_this = get_or_create_annual(session, vehicle=vehicle2, year=this_year)
    annual2_this.attempt_count = 0
    annual2_this.status = AnnualStatus.PENDING

    ap2_this_time = next_week.replace(hour=10, minute=0, second=0, microsecond=0)
    ap2_this = get_or_create_appointment(
        session,
        annual=annual2_this,
        vehicle=vehicle2,
        inspector=inspector1,
        created_by=client2,
        when=ap2_this_time,
    )
    ap2_this.status = AppointmentStatus.CONFIRMED

    # CLIENT 3: Failed inspection last week, pending appointment for tomorrow
    vehicle3 = get_or_create_vehicle(
        session,
        plate="DEF456",
        owner=client3,
        make="Chevrolet",
        model="Cruze",
        year=2019,
    )

    # This year: Failed last week
    annual3_this = get_or_create_annual(session, vehicle=vehicle3, year=this_year)
    annual3_this.attempt_count = 1
    annual3_this.status = AnnualStatus.FAILED

    ap3_failed_time = last_week.replace(hour=15, minute=0, second=0, microsecond=0)
    ap3_failed = get_or_create_appointment(
        session,
        annual=annual3_this,
        vehicle=vehicle3,
        inspector=inspector2,
        created_by=client3,
        when=ap3_failed_time,
    )
    ap3_failed.status = AppointmentStatus.COMPLETED

    scores_client3_failed = [4, 3, 5, 4, 3, 6, 5, 4]  # total 34 -> failed
    result3_failed = get_or_create_result_with_items(
        session,
        annual=annual3_this,
        appointment=ap3_failed,
        templates=templates,
        scores=scores_client3_failed,
        owner_observation_if_low_total="Frenos y luces requieren atención inmediata.",
    )
    session.flush()

    # Pending appointment for tomorrow
    ap3_tomorrow_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
    ap3_tomorrow = get_or_create_appointment(
        session,
        annual=annual3_this,
        vehicle=vehicle3,
        inspector=inspector1,
        created_by=client3,
        when=ap3_tomorrow_time,
    )
    ap3_tomorrow.status = AppointmentStatus.CONFIRMED
    annual3_this.attempt_count = 2

    # CLIENT 4: Vehicle registered but no appointments or revisions
    vehicle4 = get_or_create_vehicle(
        session,
        plate="GHI789",
        owner=client4,
        make="Ford",
        model="Focus",
        year=2021,
    )

    session.commit()
    print("Datos de demostración listos.")


if __name__ == "__main__":
    main()
