from app.db.base import Base, engine


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
