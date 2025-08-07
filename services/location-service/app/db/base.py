from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declarative_base
import os

# Get database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://devuser:devpass@postgres:5432/locationdb"
)

# Create SQLAlchemy engine with PostGIS support
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
