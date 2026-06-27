from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.application import Application
from backend.app.models.candidate import Candidate
from backend.app.models.job import Job
from backend.app.models.match import Match
from backend.app.services.application_service import (
    ApplicationDraftService,
    application_to_dict,
)


router = APIRouter()


class ApplicationDraftRequest(BaseModel):
    candidate_id: int
    job_id: int
    match_score: Optional[float] = None
    force_refresh: bool = False
    status: Optional[str] = None


class ApplicationUpdateRequest(BaseModel):
    application_text: Optional[str] = None
    cv_file_path: Optional[str] = None
    status: Optional[str] = None
    approved_by: Optional[str] = None


class ApplicationDecisionRequest(BaseModel):
    comment: Optional[str] = None
    approved_by: str = "admin"


VALID_STATUSES = {"draft", "pending_approval", "approved", "sent", "rejected"}


@router.get("/")
def get_applications(
    candidate_id: Optional[int] = None,
    job_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    query = db.query(Application)
    if candidate_id:
        query = query.filter(Application.candidate_id == candidate_id)
    if job_id:
        query = query.filter(Application.job_id == job_id)
    if status:
        query = query.filter(Application.status == status)

    applications = query.order_by(Application.created_at.desc()).all()
    return [application_to_dict(application, db) for application in applications]


@router.get("/{application_id}")
def get_application(application_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    application = _get_application_or_404(db, application_id)
    return application_to_dict(application, db)


@router.post("/draft")
def draft_application(
    payload: ApplicationDraftRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if payload.status and payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid application status")

    candidate = db.query(Candidate).filter(Candidate.id == payload.candidate_id).first()
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or job not found")

    match_score = payload.match_score
    if match_score is None:
        match = (
            db.query(Match)
            .filter(
                Match.candidate_id == candidate.id,
                Match.job_id == job.id,
            )
            .order_by(Match.created_at.desc())
            .first()
        )
        match_score = float(match.match_percentage) if match else 0.0

    service = ApplicationDraftService()
    application = service.draft_for_candidate_job(
        db,
        candidate,
        job,
        match_score,
        force_refresh=payload.force_refresh,
        status=payload.status,
    )
    return application_to_dict(application, db)


@router.patch("/{application_id}")
def update_application(
    application_id: int,
    payload: ApplicationUpdateRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if payload.status and payload.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid application status")

    application = _get_application_or_404(db, application_id)
    if hasattr(payload, "model_dump"):
        update_data = payload.model_dump(exclude_unset=True)
    else:
        update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(application, field, value)

    db.commit()
    db.refresh(application)
    return application_to_dict(application, db)


@router.post("/{application_id}/approve")
def approve_application(
    application_id: int,
    payload: ApplicationDecisionRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    application = _get_application_or_404(db, application_id)
    service = ApplicationDraftService()
    application = service.approve_application(
        db,
        application,
        approved_by=payload.approved_by,
        comment=payload.comment,
    )
    return application_to_dict(application, db)


@router.post("/{application_id}/reject")
def reject_application(
    application_id: int,
    payload: ApplicationDecisionRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    application = _get_application_or_404(db, application_id)
    service = ApplicationDraftService()
    application = service.reject_application(db, application, comment=payload.comment)
    return application_to_dict(application, db)


@router.post("/{application_id}/mark-sent")
def mark_application_sent(
    application_id: int,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    application = _get_application_or_404(db, application_id)
    if application.status not in {"approved", "sent"}:
        raise HTTPException(status_code=400, detail="Application must be approved before it is marked sent")

    service = ApplicationDraftService()
    application = service.mark_sent(db, application)
    return application_to_dict(application, db)


def _get_application_or_404(db: Session, application_id: int) -> Application:
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    return application
