from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from datetime import datetime
from backend.app.database import Base

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, index=True)
    task_name = Column(String, index=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    status = Column(String) # success, failure, started
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
