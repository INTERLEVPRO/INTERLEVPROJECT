from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.agent_log import AgentLog

router = APIRouter()

@router.get("/")
def get_agent_logs(db: Session = Depends(get_db)):
    """Fetch all agent logs for auditing."""
    logs = db.query(AgentLog).order_by(AgentLog.created_at.desc()).all()
    return [
        {
            "id": log.id,
            "agent_name": log.agent_name,
            "task_name": log.task_name,
            "action": log.task_name,
            "input_data": log.input_data,
            "output_data": log.output_data,
            "status": log.status,
            "error_message": log.error_message,
            "created_at": log.created_at,
        }
        for log in logs
    ]
