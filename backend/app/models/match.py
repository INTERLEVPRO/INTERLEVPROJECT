from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    match_percentage = Column(Float)
    match_level = Column(String) # Strong Match, Good Match, Possible Match, Poor Match
    matched_skills = Column(JSON, default=[])
    missing_skills = Column(JSON, default=[])
    reason = Column(Text, nullable=True)
    status = Column(String, default="pending") # pending, reviewed, accepted, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
