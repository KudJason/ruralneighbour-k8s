import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.session import get_db

# Test database URL - using SQLite in-memory database for tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_payment.db"

# Create test engine
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create test session factory
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """Create test database tables at the beginning of test session"""
    # Import all models to ensure they are registered with Base.metadata
    from app.models.payment import Payment, PaymentHistory, Refund
    from app.models.payment_method import UserPaymentMethod, PaymentMethodUsage

    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    yield
    # Clean up tables after all tests
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def clean_database():
    """Clean database before each test for isolation"""
    # Clean all data before each test
    with test_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()
    yield


@pytest.fixture
def db_session():
    """Provide a test database session"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def mock_get_db(db_session):
    """Mock the get_db dependency to return our test session"""

    def _get_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup is handled by db_session fixture

    return _get_db


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

        def xread(self, streams, count=10, block=1000):
            # Mock implementation for xread
            result = []
            for stream_name, stream_id in streams.items():
                if stream_name in self.streams and self.streams[stream_name]:
                    result.append((stream_name, self.streams[stream_name]))
            return result

        def close(self):
            pass

    return MockRedis()


# Override Redis client for testing
@pytest.fixture(autouse=True)
def override_redis(monkeypatch, mock_redis):
    """Override Redis client for all tests"""
    from app.services.events import EventPublisher
    from app.services.events import EventConsumer

    monkeypatch.setattr(EventPublisher, "get_redis_client", lambda: mock_redis)
    monkeypatch.setattr(EventConsumer, "get_redis_client", lambda: mock_redis)
