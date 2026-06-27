from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from backend.app.database import Base

class ReviewItem(Base):
    __tablename__ = "review_items"

    id = Column(Integer, primary_key=True, index=True)
    item_type = Column(String) # low_confidence_parse, low_match_score, incomplete_profile, etc.
    related_entity_type = Column(String) # candidate, job, match, application
    related_entity_id = Column(Integer)
    reason = Column(Text)
    status = Column(String, default="pending") # pending, resolved, dismissed
    admin_comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
