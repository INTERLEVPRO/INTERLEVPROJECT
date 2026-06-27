from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class CV(Base):
    __tablename__ = "cvs"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"), nullable=True)
    original_file_path = Column(String)
    parsed_text = Column(Text, nullable=True)
    formatted_cv_path = Column(String, nullable=True)
    parse_confidence = Column(Float, default=0.0)
    status = Column(String, default="uploaded") # uploaded, parsing, parsed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="cvs")
