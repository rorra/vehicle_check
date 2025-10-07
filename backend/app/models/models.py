from __future__ import annotations
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    Boolean,
    Enum,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    CHAR,
    text,
)
from sqlalchemy.orm import relationship, backref
from app.core.database import Base


# Enums
class UserRole(enum.Enum):
    CLIENT = "CLIENT"
    INSPECTOR = "INSPECTOR"
    ADMIN = "ADMIN"


class AnnualStatus(enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    PASSED = "PASSED"
    FAILED = "FAILED"


class AppointmentStatus(enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CreatedChannel(enum.Enum):
    CLIENT_PORTAL = "CLIENT_PORTAL"
    ADMIN_PANEL = "ADMIN_PANEL"


def ts_created():
    return Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )


def ts_updated():
    return Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# Models
class User(Base):
    __tablename__ = "users"

    id = Column(CHAR(36), primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, nullable=False, index=True)
    role = Column(Enum(UserRole, native_enum=True), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, server_default=text("1"))
    last_login_at = Column(DateTime, nullable=True)

    created_at = ts_created()
    updated_at = ts_updated()

    sessions = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    vehicles = relationship(
        "Vehicle",
        back_populates="owner",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    inspector_profile = relationship(
        "Inspector",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    created_appointments = relationship(
        "Appointment",
        back_populates="created_by_user",
        foreign_keys="Appointment.created_by_user_id",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role.value}>"


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (
        UniqueConstraint("token", name="uq_session_token"),
    )

    id = Column(CHAR(36), primary_key=True)
    user_id = Column(
        CHAR(36),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    token = Column(String(500), nullable=False)
    created_at = ts_created()
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession id={self.id} user_id={self.user_id}>"


class Inspector(Base):
    __tablename__ = "inspectors"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_inspector_user"),
        UniqueConstraint("employee_id", name="uq_inspector_employee"),
    )

    id = Column(CHAR(36), primary_key=True)
    user_id = Column(
        CHAR(36),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    employee_id = Column(String(50), nullable=False)
    active = Column(Boolean, nullable=False, server_default=text("1"))

    created_at = ts_created()
    updated_at = ts_updated()

    user = relationship("User", back_populates="inspector_profile")

    appointments = relationship(
        "Appointment",
        back_populates="inspector",
    )

    def __repr__(self) -> str:
        return f"<Inspector id={self.id} employee_id={self.employee_id} active={self.active}>"


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (
        UniqueConstraint("plate_number", name="uq_vehicles_plate"),
    )

    id = Column(CHAR(36), primary_key=True)
    plate_number = Column(String(20), nullable=False)
    make = Column(String(60), nullable=True)
    model = Column(String(60), nullable=True)
    year = Column(Integer, nullable=True)
    owner_id = Column(
        CHAR(36),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    is_active = Column(Boolean, nullable=False, server_default=text("1"))

    created_at = ts_created()
    updated_at = ts_updated()

    owner = relationship("User", back_populates="vehicles")

    annual_inspections = relationship(
        "AnnualInspection",
        back_populates="vehicle",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    appointments = relationship(
        "Appointment",
        back_populates="vehicle",
    )

    def __repr__(self) -> str:
        return f"<Vehicle id={self.id} plate={self.plate_number}>"


class AnnualInspection(Base):
    __tablename__ = "annual_inspections"
    __table_args__ = (
        UniqueConstraint("vehicle_id", "year", name="uq_annual_vehicle_year"),
    )

    id = Column(CHAR(36), primary_key=True)
    vehicle_id = Column(
        CHAR(36),
        ForeignKey("vehicles.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    year = Column(Integer, nullable=False)
    status = Column(Enum(AnnualStatus, native_enum=True), nullable=False, server_default=text("'PENDING'"))
    attempt_count = Column(Integer, nullable=False, server_default=text("0"))
    current_result_id = Column(
        CHAR(36),
        ForeignKey("inspection_results.id", onupdate="CASCADE", ondelete="SET NULL", use_alter=True, name="fk_annual_current_result"),
        nullable=True,
    )

    created_at = ts_created()
    updated_at = ts_updated()

    vehicle = relationship("Vehicle", back_populates="annual_inspections")

    current_result = relationship(
        "InspectionResult",
        foreign_keys=[current_result_id],
        backref=backref("is_current_for", uselist=False),
    )

    appointments = relationship(
        "Appointment",
        back_populates="annual_inspection",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    inspection_results = relationship(
        "InspectionResult",
        back_populates="annual_inspection",
        cascade="all, delete-orphan",
        passive_deletes=True,
        foreign_keys="InspectionResult.annual_inspection_id",
    )

    def __repr__(self) -> str:
        return f"<AnnualInspection id={self.id} vehicle_id={self.vehicle_id} year={self.year} status={self.status.value}>"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(CHAR(36), primary_key=True)
    annual_inspection_id = Column(
        CHAR(36),
        ForeignKey("annual_inspections.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    vehicle_id = Column(
        CHAR(36),
        ForeignKey("vehicles.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    inspector_id = Column(
        CHAR(36),
        ForeignKey("inspectors.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_user_id = Column(
        CHAR(36),
        ForeignKey("users.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    created_channel = Column(Enum(CreatedChannel, native_enum=True), nullable=False)
    date_time = Column(DateTime, nullable=False)
    status = Column(Enum(AppointmentStatus, native_enum=True), nullable=False, server_default=text("'PENDING'"))
    confirmation_token = Column(String(64), nullable=True)

    created_at = ts_created()
    updated_at = ts_updated()

    annual_inspection = relationship("AnnualInspection", back_populates="appointments")
    vehicle = relationship("Vehicle", back_populates="appointments")
    inspector = relationship("Inspector", back_populates="appointments")
    created_by_user = relationship("User", back_populates="created_appointments", foreign_keys=[created_by_user_id])
    inspection_result = relationship(
        "InspectionResult",
        back_populates="appointment",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Appointment id={self.id} vehicle_id={self.vehicle_id} date_time={self.date_time} status={self.status.value}>"


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="chk_slot_time_order"),
    )

    id = Column(CHAR(36), primary_key=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_booked = Column(Boolean, nullable=False, server_default=text("0"))

    created_at = ts_created()
    updated_at = ts_updated()

    def __repr__(self) -> str:
        return f"<AvailabilitySlot id={self.id} {self.start_time}..{self.end_time} booked={self.is_booked}>"


class InspectionResult(Base):
    __tablename__ = "inspection_results"
    __table_args__ = (
        UniqueConstraint("appointment_id", name="uq_results_appointment"),
        CheckConstraint("total_score BETWEEN 0 AND 80", name="chk_total_score_0_80"),
    )

    id = Column(CHAR(36), primary_key=True)
    annual_inspection_id = Column(
        CHAR(36),
        ForeignKey("annual_inspections.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    appointment_id = Column(
        CHAR(36),
        ForeignKey("appointments.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    total_score = Column(Integer, nullable=False)
    owner_observation = Column(Text, nullable=True)

    created_at = ts_created()
    updated_at = ts_updated()

    annual_inspection = relationship(
        "AnnualInspection",
        back_populates="inspection_results",
        foreign_keys=[annual_inspection_id],
    )
    appointment = relationship("Appointment", back_populates="inspection_result")
    item_checks = relationship(
        "ItemCheck",
        back_populates="inspection_result",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<InspectionResult id={self.id} total_score={self.total_score}>"


class CheckItemTemplate(Base):
    __tablename__ = "check_item_templates"
    __table_args__ = (
        UniqueConstraint("code", name="uq_check_item_code"),
        UniqueConstraint("ordinal", name="uq_check_item_ordinal"),
        CheckConstraint("ordinal BETWEEN 1 AND 8", name="chk_template_ordinal_1_8"),
    )

    id = Column(CHAR(36), primary_key=True)
    code = Column(String(30), nullable=False)
    description = Column(String(255), nullable=False)
    ordinal = Column(Integer, nullable=False)

    created_at = ts_created()
    updated_at = ts_updated()

    item_checks = relationship("ItemCheck", back_populates="template")

    def __repr__(self) -> str:
        return f"<CheckItemTemplate id={self.id} code={self.code} ordinal={self.ordinal}>"


class ItemCheck(Base):
    __tablename__ = "item_checks"
    __table_args__ = (
        UniqueConstraint("inspection_result_id", "check_item_template_id", name="uq_item_per_result"),
        CheckConstraint("score BETWEEN 1 AND 10", name="chk_item_score_1_10"),
    )

    id = Column(CHAR(36), primary_key=True)
    inspection_result_id = Column(
        CHAR(36),
        ForeignKey("inspection_results.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    check_item_template_id = Column(
        CHAR(36),
        ForeignKey("check_item_templates.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    score = Column(Integer, nullable=False)  # 1..10 (Validated by CheckConstraint)
    observation = Column(String(500), nullable=True)

    created_at = ts_created()
    updated_at = ts_updated()

    inspection_result = relationship("InspectionResult", back_populates="item_checks")
    template = relationship("CheckItemTemplate", back_populates="item_checks")

    def __repr__(self) -> str:
        return (
            f"<ItemCheck id={self.id} result_id={self.inspection_result_id} "
            f"template_id={self.check_item_template_id} score={self.score}>"
        )
