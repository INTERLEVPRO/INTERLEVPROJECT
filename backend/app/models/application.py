from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from datetime import datetime
from backend.app.database import Base

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    job_id = Column(Integer, ForeignKey("jobs.id"))
    application_text = Column(Text, nullable=True)
    cv_file_path = Column(String, nullable=True)
    status = Column(String, default="draft") # draft, pending_approval, approved, sent, rejected
    approved_by = Column(String, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
