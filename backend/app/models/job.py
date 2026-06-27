from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    company = Column(String, index=True)
    platform = Column(String, nullable=True) # Hays, Gulp, etc.
    url = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    required_skills = Column(JSON, default=[])
    nice_to_have_skills = Column(JSON, default=[])
    budget = Column(String, nullable=True)
    location = Column(String, nullable=True)
    contract_type = Column(String, nullable=True) # Remote, Freelance, etc.
    posted_date = Column(DateTime, nullable=True)
    status = Column(String, default="active") # active, expired, filled
    created_at = Column(DateTime, default=datetime.utcnow)
