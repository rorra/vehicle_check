"""Data factories for testing using factory_boy and faker."""
import factory
from factory import fuzzy
from faker import Faker
from datetime import datetime, timezone, timedelta
from app.models import (
    User, UserRole, UserSession, Inspector, Vehicle, AnnualInspection,
    AnnualStatus, Appointment, AppointmentStatus, CreatedChannel,
    AvailabilitySlot, InspectionResult, CheckItemTemplate, ItemCheck,
    generate_uuid
)

fake = Faker()


class UserFactory(factory.Factory):
    """Factory for User model."""
    class Meta:
        model = User

    id = factory.LazyFunction(generate_uuid)
    name = factory.Faker('name')
    email = factory.LazyAttribute(lambda obj: f"{fake.uuid4()}@{fake.domain_name()}")
    role = fuzzy.FuzzyChoice([UserRole.CLIENT, UserRole.INSPECTOR, UserRole.ADMIN])
    password_hash = factory.LazyFunction(lambda: "hashed_password")
    is_active = True
    last_login_at = None


class ClientUserFactory(UserFactory):
    """Factory for client users."""
    role = UserRole.CLIENT
    name = factory.Faker('name')


class InspectorUserFactory(UserFactory):
    """Factory for inspector users."""
    role = UserRole.INSPECTOR
    name = factory.Faker('name')


class AdminUserFactory(UserFactory):
    """Factory for admin users."""
    role = UserRole.ADMIN
    name = factory.Faker('name')


class UserSessionFactory(factory.Factory):
    """Factory for UserSession model."""
    class Meta:
        model = UserSession

    id = factory.LazyFunction(generate_uuid)
    user_id = factory.LazyFunction(generate_uuid)
    token = factory.Faker('sha256')
    expires_at = factory.LazyFunction(lambda: datetime.now(timezone.utc) + timedelta(minutes=30))
    revoked_at = None


class InspectorFactory(factory.Factory):
    """Factory for Inspector model."""
    class Meta:
        model = Inspector

    id = factory.LazyFunction(generate_uuid)
    user_id = factory.LazyFunction(generate_uuid)
    employee_id = factory.LazyAttribute(lambda obj: f"INS-{fake.uuid4()[:8].upper()}")
    active = True


class VehicleFactory(factory.Factory):
    """Factory for Vehicle model."""
    class Meta:
        model = Vehicle

    id = factory.LazyFunction(generate_uuid)
    plate_number = factory.LazyAttribute(lambda obj: f"{fake.random_uppercase_letter()}{fake.random_uppercase_letter()}{fake.random_uppercase_letter()}-{fake.random_int(min=1000, max=9999)}")
    make = factory.Faker('company')
    model = factory.Faker('word')
    year = fuzzy.FuzzyInteger(2000, 2024)
    owner_id = factory.LazyFunction(generate_uuid)


class AnnualInspectionFactory(factory.Factory):
    """Factory for AnnualInspection model."""
    class Meta:
        model = AnnualInspection

    id = factory.LazyFunction(generate_uuid)
    vehicle_id = factory.LazyFunction(generate_uuid)
    year = fuzzy.FuzzyInteger(2020, 2025)
    status = fuzzy.FuzzyChoice([AnnualStatus.PENDING, AnnualStatus.IN_PROGRESS, AnnualStatus.PASSED, AnnualStatus.FAILED])
    attempt_count = 0
    current_result_id = None


class AppointmentFactory(factory.Factory):
    """Factory for Appointment model."""
    class Meta:
        model = Appointment

    id = factory.LazyFunction(generate_uuid)
    annual_inspection_id = factory.LazyFunction(generate_uuid)
    vehicle_id = factory.LazyFunction(generate_uuid)
    inspector_id = None
    created_by_user_id = factory.LazyFunction(generate_uuid)
    created_channel = fuzzy.FuzzyChoice([CreatedChannel.CLIENT_PORTAL, CreatedChannel.ADMIN_PANEL])
    date_time = factory.LazyFunction(lambda: datetime.now(timezone.utc) + timedelta(days=7))
    status = fuzzy.FuzzyChoice([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED])
    confirmation_token = None


class AvailabilitySlotFactory(factory.Factory):
    """Factory for AvailabilitySlot model."""
    class Meta:
        model = AvailabilitySlot

    id = factory.LazyFunction(generate_uuid)
    start_time = factory.LazyFunction(lambda: datetime.now(timezone.utc) + timedelta(days=1))
    end_time = factory.LazyAttribute(lambda obj: obj.start_time + timedelta(hours=1))
    is_booked = False


class InspectionResultFactory(factory.Factory):
    """Factory for InspectionResult model."""
    class Meta:
        model = InspectionResult

    id = factory.LazyFunction(generate_uuid)
    annual_inspection_id = factory.LazyFunction(generate_uuid)
    appointment_id = factory.LazyFunction(generate_uuid)
    total_score = fuzzy.FuzzyInteger(40, 80)
    owner_observation = factory.Faker('sentence')


class CheckItemTemplateFactory(factory.Factory):
    """Factory for CheckItemTemplate model."""
    class Meta:
        model = CheckItemTemplate

    id = factory.LazyFunction(generate_uuid)
    code = factory.LazyAttribute(lambda obj: f"{fake.random_uppercase_letter()}{fake.random_uppercase_letter()}{fake.random_uppercase_letter()}")
    description = factory.Faker('sentence')
    ordinal = fuzzy.FuzzyInteger(1, 8)


class ItemCheckFactory(factory.Factory):
    """Factory for ItemCheck model."""
    class Meta:
        model = ItemCheck

    id = factory.LazyFunction(generate_uuid)
    inspection_result_id = factory.LazyFunction(generate_uuid)
    check_item_template_id = factory.LazyFunction(generate_uuid)
    score = fuzzy.FuzzyInteger(1, 10)
    observation = factory.Faker('sentence')
