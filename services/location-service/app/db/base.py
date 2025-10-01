import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import declarative_base, sessionmaker

# Choose database URL. In TESTING mode default to SQLite to avoid external deps
if os.getenv("TESTING") == "true" and not os.getenv("DATABASE_URL"):
    DATABASE_URL = "sqlite:///./test_location_service.db"
else:
    # Get database URL from environment variable or construct from individual components
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # Construct from individual environment variables
        db_user = os.getenv("POSTGRES_USER", "devuser")
        db_password = os.getenv("POSTGRES_PASSWORD", "devpass")
        db_host = os.getenv("POSTGRES_HOST", "postgres")
        db_port = os.getenv("POSTGRES_PORT", "5432")
        db_name = os.getenv("POSTGRES_DB", "locationdb")
        DATABASE_URL = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
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
