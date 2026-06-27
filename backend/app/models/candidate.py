from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    main_role = Column(String, nullable=True)
    experience_years = Column(Integer, default=0)
    experience_level = Column(String, default="Junior") # Junior, Mid, Senior
    availability = Column(String, nullable=True)
    expected_rate = Column(String, nullable=True)
    profile_status = Column(String, default="incomplete") # incomplete, complete, verified
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    skills = relationship("CandidateSkill", back_populates="candidate")
    cvs = relationship("CV", back_populates="candidate")

class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    skill_name = Column(String, index=True)
    skill_level = Column(String, nullable=True) # beginner, intermediate, expert
    years_experience = Column(Integer, default=0)

    candidate = relationship("Candidate", back_populates="skills")
