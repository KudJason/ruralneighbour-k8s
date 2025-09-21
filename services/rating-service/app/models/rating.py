from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, CheckConstraint, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from ..db.base import Base
import os
import uuid


class Rating(Base):
    __tablename__ = "ratings"

    # 根据数据库类型选择不同的字段类型
    if os.getenv("TESTING") == "true" or "sqlite" in os.getenv("DATABASE_URL", ""):
        # SQLite 兼容
        id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
        rated_user_id = Column(String(36), nullable=False)
        rater_user_id = Column(String(36), nullable=False)
        service_request_id = Column(String(36), nullable=False)
        data = Column(JSON, default={})
    else:
        # PostgreSQL
        id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
        rated_user_id = Column(UUID(as_uuid=True), nullable=False)
        rater_user_id = Column(UUID(as_uuid=True), nullable=False)
        service_request_id = Column(UUID(as_uuid=True), nullable=False)
        data = Column(JSONB, default={})
    
    rating_score = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 约束
    __table_args__ = (
        CheckConstraint('rating_score >= 1 AND rating_score <= 5', name='check_rating_score_range'),
        UniqueConstraint('rater_user_id', 'service_request_id', name='unique_rating_per_request'),
    )

    def __repr__(self):
        return f"<Rating(id={self.id}, rating_score={self.rating_score}, rated_user_id={self.rated_user_id})>"
