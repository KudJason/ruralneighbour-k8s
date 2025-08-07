import pytest
from app.db.base import engine, Base
from app.models.profile import UserProfile, ProviderProfile


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """自动创建所有模型表，确保测试环境完整"""
    Base.metadata.create_all(bind=engine)
    yield
    # 可选：测试结束后清理表
    # Base.metadata.drop_all(bind=engine)
