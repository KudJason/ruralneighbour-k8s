from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment variable
# For production: DATABASE_URL=postgresql://user:password@host:port/dbname
# For testing: DATABASE_URL=sqlite:///./test.db
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://devuser:devpass@postgres:5432/request_service"
)

# Create SQLAlchemy engine
if "sqlite" in DATABASE_URL:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import Base class
from app.db.base_class import Base

# Import all models to register them with SQLAlchemy
from app.models.service_request import ServiceRequest, ServiceAssignment, Rating


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
