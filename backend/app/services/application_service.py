from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from backend.app.agents.application_writer_agent import ApplicationWriterAgent
from backend.app.agents.logging_agent import LoggingAgent
from backend.app.agents.notification_agent import NotificationAgent
from backend.app.models.application import Application
from backend.app.models.candidate import Candidate
from backend.app.models.cv import CV
from backend.app.models.job import Job
from backend.app.models.review import ReviewItem
from backend.app.services.app_settings import load_settings
from backend.app.services.llm.factory import get_llm_provider


def application_to_dict(application: Application, db: Optional[Session] = None) -> Dict[str, Any]:
    candidate = None
    job = None
    if db:
        candidate = db.query(Candidate).filter(Candidate.id == application.candidate_id).first()
        job = db.query(Job).filter(Job.id == application.job_id).first()

    return {
        "id": application.id,
        "candidate_id": application.candidate_id,
        "job_id": application.job_id,
        "application_text": application.application_text,
        "cv_file_path": application.cv_file_path,
        "status": application.status,
        "approved_by": application.approved_by,
        "sent_at": application.sent_at,
        "created_at": application.created_at,
        "candidate_name": candidate.name if candidate else None,
        "job_title": job.title if job else None,
        "company": job.company if job else None,
        "job_url": job.url if job else None,
    }


class ApplicationDraftService:
    def __init__(self):
        self.llm = get_llm_provider()
        self.writer = ApplicationWriterAgent(self.llm)

    def draft_for_candidate_job(
        self,
        db: Session,
        candidate: Candidate,
        job: Job,
        match_score: float,
        force_refresh: bool = False,
        status: Optional[str] = None,
    ) -> Application:
        existing = (
            db.query(Application)
            .filter(
                Application.candidate_id == candidate.id,
                Application.job_id == job.id,
            )
            .order_by(Application.created_at.desc())
            .first()
        )

        if existing and not force_refresh:
            return existing

        draft = self.writer.draft_application(candidate, job, match_score)
        application_text = self._format_application_text(draft)
        formatted_cv = self._latest_formatted_cv(db, candidate.id)
        application_status = status or self._initial_status()

        if existing:
            application = existing
            application.application_text = application_text
            application.cv_file_path = formatted_cv
            application.status = application_status
            application.approved_by = None
            application.sent_at = None
        else:
            application = Application(
                candidate_id=candidate.id,
                job_id=job.id,
                application_text=application_text,
                cv_file_path=formatted_cv,
                status=application_status,
            )
            db.add(application)

        db.flush()
        LoggingAgent.log_action(
            db,
            "Application Writer",
            "Drafting Application",
            "success",
            input_data={
                "candidate_id": candidate.id,
                "job_id": job.id,
                "match_score": match_score,
            },
            output_data={
                "application_id": application.id,
                "status": application.status,
            },
        )
        NotificationAgent.notify(
            db,
            "Application draft ready",
            f"Draft created for {candidate.name} applying to {job.title}.",
            "success" if application.status != "pending_approval" else "info",
            "application",
            {
                "application_id": application.id,
                "candidate_id": candidate.id,
                "job_id": job.id,
                "status": application.status,
            },
        )
        self._ensure_review_item(db, application)
        db.commit()
        db.refresh(application)
        return application

    def approve_application(
        self,
        db: Session,
        application: Application,
        approved_by: str = "admin",
        comment: Optional[str] = None,
    ) -> Application:
        application.status = "approved"
        application.approved_by = approved_by
        self._resolve_review_items(db, application.id, "resolved", comment or "Application approved")
        NotificationAgent.notify(
            db,
            "Application approved",
            f"Application #{application.id} is approved and ready to send.",
            "success",
            "application",
            {"application_id": application.id},
        )
        db.commit()
        db.refresh(application)
        return application

    def reject_application(
        self,
        db: Session,
        application: Application,
        comment: Optional[str] = None,
    ) -> Application:
        application.status = "rejected"
        self._resolve_review_items(db, application.id, "dismissed", comment or "Application rejected")
        NotificationAgent.notify(
            db,
            "Application rejected",
            f"Application #{application.id} was rejected.",
            "warning",
            "application",
            {"application_id": application.id},
        )
        db.commit()
        db.refresh(application)
        return application

    def mark_sent(self, db: Session, application: Application) -> Application:
        application.status = "sent"
        application.sent_at = datetime.utcnow()
        NotificationAgent.notify(
            db,
            "Application marked sent",
            f"Application #{application.id} was marked as sent.",
            "success",
            "application",
            {"application_id": application.id},
        )
        db.commit()
        db.refresh(application)
        return application

    def _format_application_text(self, draft: Dict[str, Any]) -> str:
        return (
            f"Subject: {draft.get('email_subject', '')}\n\n"
            f"{draft.get('email_body', '')}\n\n"
            "Portal Message:\n"
            f"{draft.get('portal_message', '')}"
        ).strip()

    def _initial_status(self) -> str:
        settings = load_settings()
        if settings.automation.autonomy_level == "draft_only":
            return "draft"
        if (
            settings.automation.autonomy_level == "fully_autonomous"
            and not settings.automation.human_review_required
        ):
            return "approved"
        return "pending_approval"

    def _latest_formatted_cv(self, db: Session, candidate_id: int) -> Optional[str]:
        cv = (
            db.query(CV)
            .filter(CV.candidate_id == candidate_id)
            .order_by(CV.created_at.desc())
            .first()
        )
        if not cv:
            return None
        return cv.formatted_cv_path or cv.original_file_path

    def _ensure_review_item(self, db: Session, application: Application) -> None:
        if application.status != "pending_approval":
            return

        existing = (
            db.query(ReviewItem)
            .filter(
                ReviewItem.related_entity_type == "application",
                ReviewItem.related_entity_id == application.id,
                ReviewItem.status == "pending",
            )
            .first()
        )
        if existing:
            return

        db.add(
            ReviewItem(
                item_type="application_approval",
                related_entity_type="application",
                related_entity_id=application.id,
                reason="Application draft requires approval before sending.",
            )
        )

    def _resolve_review_items(
        self,
        db: Session,
        application_id: int,
        status: str,
        comment: str,
    ) -> None:
        review_items = (
            db.query(ReviewItem)
            .filter(
                ReviewItem.related_entity_type == "application",
                ReviewItem.related_entity_id == application_id,
                ReviewItem.status == "pending",
            )
            .all()
        )
        for item in review_items:
            item.status = status
            item.admin_comment = comment
