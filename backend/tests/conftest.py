import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.core.database import Base, get_db
from app.core.config import settings
from app.models import *
from app.main import app
from tests.factories import (
    ClientUserFactory, AdminUserFactory, InspectorUserFactory,
    VehicleFactory, InspectorFactory, CheckItemTemplateFactory
)


def utc_now():
    """Get current UTC time in a timezone-aware manner."""
    return datetime.now(timezone.utc)


@pytest.fixture(scope="function")
def db_session():
    """Create a MySQL test database for testing."""
    engine = create_engine(settings.DATABASE_TEST_URL)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = ClientUserFactory.build()
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_inspector_user(db_session):
    """Create a sample inspector user for testing."""
    user = InspectorUserFactory.build()
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_inspector(db_session, sample_inspector_user):
    """Create a sample inspector profile for testing."""
    inspector = InspectorFactory.build(user_id=sample_inspector_user.id)
    db_session.add(inspector)
    db_session.commit()
    return inspector


@pytest.fixture
def sample_vehicle(db_session, sample_user):
    """Create a sample vehicle for testing."""
    vehicle = VehicleFactory.build(owner_id=sample_user.id)
    db_session.add(vehicle)
    db_session.commit()
    return vehicle


@pytest.fixture
def sample_check_templates(db_session):
    """Create the 8 standard check item templates."""
    templates_data = [
        ("BRK", "Frenos"),
        ("LGT", "Luces e indicadores"),
        ("TIR", "Neumáticos"),
        ("ENG", "Motor y fugas"),
        ("STE", "Dirección"),
        ("SUS", "Suspensión"),
        ("EMI", "Emisiones"),
        ("SAF", "Elementos de seguridad"),
    ]

    templates = []
    for idx, (code, desc) in enumerate(templates_data, start=1):
        template = CheckItemTemplateFactory.build(
            code=code,
            description=desc,
            ordinal=idx,
        )
        db_session.add(template)
        templates.append(template)

    db_session.commit()
    return templates


@pytest.fixture
def client_user(db_session):
    """Create a client user for testing."""
    from app.core.security import get_password_hash
    user = ClientUserFactory.build(
        name="Client User",
        password_hash=get_password_hash("password")
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    from app.core.security import get_password_hash
    user = AdminUserFactory.build(
        name="Admin User",
        password_hash=get_password_hash("password")
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def inspector_user(db_session):
    """Create an inspector user for testing."""
    from app.core.security import get_password_hash
    user = InspectorUserFactory.build(
        name="Inspector User",
        password_hash=get_password_hash("password")
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def client_token(client, db_session, client_user):
    """Create an auth token for the client user."""
    from datetime import timedelta
    from app.core.security import create_access_token
    from app.core.config import settings
    token = create_access_token({"sub": client_user.id, "email": client_user.email})
    # Create session
    session = UserSession(
        id=generate_uuid(),
        user_id=client_user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        revoked_at=None,
    )
    db_session.add(session)
    db_session.commit()
    return token


@pytest.fixture
def admin_token(client, db_session, admin_user):
    """Create an auth token for the admin user."""
    from datetime import timedelta
    from app.core.security import create_access_token
    from app.core.config import settings
    token = create_access_token({"sub": admin_user.id, "email": admin_user.email})
    # Create session
    session = UserSession(
        id=generate_uuid(),
        user_id=admin_user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        revoked_at=None,
    )
    db_session.add(session)
    db_session.commit()
    return token


@pytest.fixture
def inspector_token(client, db_session, inspector_user):
    """Create an auth token for the inspector user."""
    from datetime import timedelta
    from app.core.security import create_access_token
    from app.core.config import settings
    token = create_access_token({"sub": inspector_user.id, "email": inspector_user.email})
    # Create session
    session = UserSession(
        id=generate_uuid(),
        user_id=inspector_user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        revoked_at=None,
    )
    db_session.add(session)
    db_session.commit()
    return token


@pytest.fixture
def client_vehicle(db_session, client_user):
    """Create a vehicle owned by client_user"""
    vehicle = VehicleFactory.build(owner_id=client_user.id)
    db_session.add(vehicle)
    db_session.commit()
    return vehicle


@pytest.fixture
def client(db_session):
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
