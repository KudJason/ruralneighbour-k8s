import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.profile import UserProfile, ProviderProfile
from app.db.base import Base, get_db
from app.main import app  # 导入 FastAPI 实例


@pytest.fixture(scope="session")
def test_db_file():
    """Create a temporary SQLite file for testing and remove it after tests."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture(scope="session")
def engine(test_db_file):
    """Create a SQLAlchemy engine for the test SQLite database."""
    return create_engine(f"sqlite:///{test_db_file}")


@pytest.fixture(scope="session", autouse=True)
def create_test_tables(engine):
    """Create all tables in the test database before tests, and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(engine):
    """Provide a session for each test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


# 自动覆盖 FastAPI 的 get_db 依赖，确保所有 API 用测试 SQLite
@pytest.fixture(autouse=True, scope="function")
def override_get_db(db_session):
    def _get_db_override():
        yield db_session

    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.pop(get_db, None)
