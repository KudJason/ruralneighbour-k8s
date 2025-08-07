import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, Boolean, DateTime, Text, Date
import os

# Use String for UUID in testing environment
if os.getenv("TESTING") == "true":
    UUIDType = String(36)  # UUID as string

    def uuid_default():
        return str(uuid.uuid4())

else:
    from sqlalchemy.dialects.postgresql import UUID as UUIDType

    def uuid_default():
        return uuid.uuid4()


from app.db.base import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    article_id = Column(UUIDType, primary_key=True, default=uuid_default)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(UUIDType, nullable=True)  # References users(user_id)
    image_url = Column(Text, nullable=True)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    publish_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)  # For retention policy
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<NewsArticle(article_id={self.article_id}, title={self.title}, is_active={self.is_active})>"
