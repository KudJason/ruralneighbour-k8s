from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Get database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://devuser:devpass@postgres:5432/notificationdb"
)

# Use SQLite for testing
if os.getenv("TESTING") == "true":
    DATABASE_URL = "sqlite:///./test_notification.db"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
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
