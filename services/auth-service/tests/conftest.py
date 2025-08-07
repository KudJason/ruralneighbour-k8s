import pytest
from sqlalchemy import create_engine
from app.db.base import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)


@pytest.fixture(autouse=True)
def clean_database():
    # Drop all tables and recreate before each test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # Optional: Drop tables after test for extra isolation
    Base.metadata.drop_all(bind=engine)
