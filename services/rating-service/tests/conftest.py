import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rating.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine

@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def sample_user_ids():
    import os
    # 在测试模式下返回字符串ID，在生产模式下返回UUID对象
    if os.getenv("TESTING") == "true" or "sqlite" in os.getenv("DATABASE_URL", ""):
        return {
            "rater_id": str(uuid4()),
            "rated_id": str(uuid4()),
            "service_request_id": str(uuid4())
        }
    else:
        return {
            "rater_id": uuid4(),
            "rated_id": uuid4(),
            "service_request_id": uuid4()
        }
