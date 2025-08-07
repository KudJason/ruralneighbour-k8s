import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import SessionLocal

# Test database configuration - use SQLite for testing
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_request_service.db"
TEST_DATABASE_URL = "sqlite:///./test_request_service.db"

# Create test engine and session
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the database URL for testing
import app.core.config as config

config.DATABASE_URL = TEST_DATABASE_URL
config.settings.DATABASE_URL = TEST_DATABASE_URL

# Create all tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def override_get_current_user_id():
    """Override authentication dependency for testing"""
    import uuid

    # Return a fixed UUID for consistent testing
    return uuid.UUID("12345678-1234-5678-9012-123456789012")


# Override the dependencies
from app.db.session import get_db
from app.api.deps import get_current_user_id

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user_id] = override_get_current_user_id

# Override the database engine and SessionLocal
import app.db.base as db_base
import app.db.session as db_session

# Replace the database engine and SessionLocal in the base module
db_base.engine = engine
db_base.SessionLocal = TestingSessionLocal


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Database session for testing"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Clean up after each test
        from app.models.service_request import Rating, ServiceAssignment, ServiceRequest

        try:
            db.rollback()  # Rollback any pending transactions
            db.query(Rating).delete()
            db.query(ServiceAssignment).delete()
            db.query(ServiceRequest).delete()
            db.commit()
        except Exception as e:
            print(f"Error during test cleanup: {e}")
            db.rollback()
        finally:
            db.close()


@pytest.fixture
def mock_redis():
    """Mock Redis for testing events"""

    class MockRedis:
        def __init__(self):
            self.streams = {}

        def xadd(self, stream_name, data):
            if stream_name not in self.streams:
                self.streams[stream_name] = []
            event_id = f"test-{len(self.streams[stream_name])}"
            self.streams[stream_name].append((event_id, data))
            return event_id

        def close(self):
            pass

    return MockRedis()


@pytest.fixture
def mock_auth_user():
    """Mock authenticated user for testing"""
    import uuid

    # Return the same UUID that's used in the override
    return uuid.UUID("12345678-1234-5678-9012-123456789012")


# Override Redis client for testing
@pytest.fixture(autouse=True)
def override_redis(monkeypatch, mock_redis):
    """Override Redis client for all tests"""
    from app.services.events import EventPublisher
    from app.services.event_consumer import EventConsumer

    monkeypatch.setattr(EventPublisher, "get_redis_client", lambda: mock_redis)
    monkeypatch.setattr(EventConsumer, "get_redis_client", lambda self: mock_redis)
