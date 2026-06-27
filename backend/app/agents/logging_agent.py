from backend.app.models.agent_log import AgentLog
from sqlalchemy.orm import Session
from typing import Any, Optional

class LoggingAgent:
    @staticmethod
    def log_action(
        db: Session,
        agent_name: str,
        task_name: str,
        status: str,
        input_data: Optional[Any] = None,
        output_data: Optional[Any] = None,
        error_message: Optional[str] = None
    ):
        """
        Centralized logging for all agent actions.
        """
        log = AgentLog(
            agent_name=agent_name,
            task_name=task_name,
            input_data=input_data,
            output_data=output_data,
            status=status,
            error_message=error_message
        )
        db.add(log)
        db.commit()
        return log
