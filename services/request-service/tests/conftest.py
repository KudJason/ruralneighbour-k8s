import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app
from app.db.base import Base
from app.db.session import get_db

# Test database configuration: use in-memory mock DB for testing
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


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

        db.query(Rating).delete()
        db.query(ServiceAssignment).delete()
        db.query(ServiceRequest).delete()
        db.commit()
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

    return uuid.uuid4()


# Override Redis client for testing
@pytest.fixture(autouse=True)
def override_redis(monkeypatch, mock_redis):
    """Override Redis client for all tests"""
    from app.services.events import EventPublisher
    from app.services.event_consumer import EventConsumer

    monkeypatch.setattr(EventPublisher, "get_redis_client", lambda: mock_redis)
    monkeypatch.setattr(EventConsumer, "get_redis_client", lambda self: mock_redis)
