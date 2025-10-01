import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 优先使用环境变量中的 DATABASE_URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://neighbor:password@localhost:5432/investment_service"
)

# 根据数据库类型设置连接参数
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
