import pytest
import os

# Set testing environment EARLY before importing app modules
os.environ["TESTING"] = "true"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_notification.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def clean_database():
    """Clean database before and after each test"""
    # Drop all tables and recreate before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Optional: Drop tables after test for extra isolation
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide a database session for tests"""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
