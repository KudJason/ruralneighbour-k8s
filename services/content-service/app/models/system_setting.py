import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text
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


class SystemSetting(Base):
    __tablename__ = "system_settings"

    setting_id = Column(UUIDType, primary_key=True, default=uuid_default)
    setting_key = Column(String(255), unique=True, nullable=False)
    setting_value = Column(Text, nullable=True)
    setting_type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<SystemSetting(setting_id={self.setting_id}, setting_key={self.setting_key})>"
