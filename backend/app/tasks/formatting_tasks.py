from backend.app.tasks.celery_app import celery_app
from backend.app.database import SessionLocal
from backend.app.agents.cv_formatter_agent import CVFormatterAgent
from backend.app.models.candidate import Candidate
from backend.app.models.cv import CV
from backend.app.agents.logging_agent import LoggingAgent
from backend.app.agents.notification_agent import NotificationAgent

@celery_app.task(name="format_cv_task")
def format_cv_task(candidate_id: int):
    db = SessionLocal()
    formatter = CVFormatterAgent()
    
    try:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            return {"status": "error", "message": "Candidate not found"}

        LoggingAgent.log_action(db, "Formatter", "Generating formatted CV", "working", input_data={"candidate_id": candidate_id})
        file_path = formatter.generate_file(candidate)
        LoggingAgent.log_action(db, "Formatter", "Generating formatted CV", "success", output_data={"file_path": file_path})
        NotificationAgent.notify(
            db,
            "CV formatted",
            f"Formatted CV created for {candidate.name}.",
            "success",
            "cv",
            {"candidate_id": candidate_id, "file_path": file_path},
        )
        
        # Update CV record
        cv_record = db.query(CV).filter(CV.candidate_id == candidate_id).first()
        if cv_record:
            cv_record.formatted_cv_path = file_path
        
        db.commit()
        return {"status": "success", "formatted_cv_path": file_path}
    except Exception as e:
        db.rollback()
        LoggingAgent.log_action(db, "Formatter", "Formatting Error", "error", error_message=str(e))
        NotificationAgent.notify(db, "CV formatting failed", str(e), "error", "cv", {"candidate_id": candidate_id})
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
