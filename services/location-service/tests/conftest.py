import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base

# Set testing environment
os.environ["TESTING"] = "true"

# Test database URL - using SQLite for testing (PostGIS features will be mocked)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_location.db"

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
    from app.models.address import UserAddress

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
def mock_postgis_point():
    """Mock PostGIS point creation for testing"""

    def create_point(latitude: float, longitude: float) -> str:
        return f"POINT({longitude} {latitude})"

    return create_point


@pytest.fixture
def sample_address_data():
    """Sample address data for testing"""
    import uuid

    return {
        "user_id": uuid.uuid4(),
        "street_address": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postal_code": "10001",
        "country": "USA",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "is_primary": False,
        "address_type": "residential",
    }
