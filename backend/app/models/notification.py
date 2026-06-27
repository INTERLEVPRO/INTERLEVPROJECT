from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from backend.app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    message = Column(Text)
    level = Column(String, default="info")
    category = Column(String, default="system")
    is_read = Column(Boolean, default=False)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
