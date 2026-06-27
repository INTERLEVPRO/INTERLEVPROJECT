from pathlib import Path
from typing import Any, Dict

from celery.result import AsyncResult
from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException, Query, Body
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.agents.cv_formatter_agent import CVFormatterAgent
from backend.app.database import get_db
from backend.app.agents.job_search_agent import JobSearchAgent
from backend.app.agents.notification_agent import NotificationAgent
from backend.app.models.candidate import Candidate
from backend.app.models.cv import CV
from backend.app.models.job import Job
from backend.app.services.app_settings import load_settings
from backend.app.tasks.celery_app import celery_app
from backend.app.tasks.cv_tasks import parse_cv_task
from backend.app.tasks.formatting_tasks import format_cv_task
import shutil

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_cv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a CV and start the parsing workflow.
    """
    file_path = _save_upload(file)

    NotificationAgent.notify(
        db,
        "CV uploaded",
        f"{file.filename} was uploaded and queued for analysis.",
        "info",
        "cv",
        {"file_path": file_path},
    )
    
    # Trigger Celery task
    task = parse_cv_task.delay(file_path)
    
    return {"message": "CV uploaded and parsing started", "task_id": task.id, "file_path": file_path}

@router.get("/")
def get_cvs(db: Session = Depends(get_db)):
    """List uploaded and parsed CV records."""
    return db.query(CV).order_by(CV.created_at.desc()).all()

@router.get("/status/{task_id}")
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Return Celery task state and result payload when available."""
    task = AsyncResult(task_id, app=celery_app)
    response: Dict[str, Any] = {
        "task_id": task_id,
        "status": task.state,
        "ready": task.ready(),
        "successful": task.successful() if task.ready() else False,
    }
    if task.ready():
        response["result"] = jsonable_encoder(task.result)
    elif task.info:
        response["info"] = jsonable_encoder(task.info)
    return response

@router.post("/run-full-campaign")
async def run_full_campaign(
    file: UploadFile = File(...),
    keywords: str = Form(""),
    source_url: str = Form(""),
    search_mode: str = Form("real_search"),
    db: Session = Depends(get_db),
):
    """
    ONE CLICK CAMPAIGN: Upload CV and run ALL agents automatically.
    """
    from backend.app.tasks.cv_tasks import run_full_recruitment_workflow

    keyword_list = [keyword.strip() for keyword in keywords.split(",") if keyword.strip()]
    clean_source_url = source_url.strip()
    clean_search_mode = (search_mode or "real_search").strip().lower()
    if clean_search_mode not in {"real_search", "fast_pass"}:
        raise HTTPException(status_code=400, detail="search_mode must be real_search or fast_pass")
    try:
        if clean_search_mode != "fast_pass":
            JobSearchAgent().validate_source_url(clean_source_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    file_path = _save_upload(file, prefix="campaign_")

    NotificationAgent.notify(
        db,
        "Campaign started",
        f"{file.filename} was uploaded. Agents will analyze the CV and search enabled websites.",
        "info",
        "campaign",
        {"file_path": file_path, "keywords": keyword_list, "source_url": clean_source_url},
    )
    task = run_full_recruitment_workflow.delay(file_path, keyword_list, clean_source_url, clean_search_mode)
    
    return {"message": "Full autonomous campaign started", "task_id": task.id, "file_path": file_path}

@router.post("/run-legacy-orchestrator")
async def run_legacy_orchestrator(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Runs the original 5-agent orchestrator with OpenAI tool calling.
    """
    from backend.agents.orchestrator import run_orchestrator
    
    file_path = _save_upload(file, prefix="legacy_")
        
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        cv_text = f.read()
        
    result = run_orchestrator("Find the best matching freelance project for my CV and draft an application.", cv_text)
    
    return {"message": "Legacy orchestrator finished", "result": result}

@router.post("/{candidate_id}/format")
def format_candidate_cv(candidate_id: int):
    """Start a background task to regenerate the formatted CV for a candidate."""
    task = format_cv_task.delay(candidate_id)
    return {"message": "CV formatting started", "task_id": task.id, "candidate_id": candidate_id}


@router.get("/candidate/{candidate_id}/job/{job_id}/preview")
def preview_candidate_job_cv(candidate_id: int, job_id: int, db: Session = Depends(get_db)):
    """Return the formatted CV preview data for a candidate tailored to a matched job."""
    candidate, job = _candidate_and_job(db, candidate_id, job_id)
    return CVFormatterAgent().build_preview(candidate, job)


@router.get("/candidate/{candidate_id}/job/{job_id}/download")
def download_candidate_job_cv(
    candidate_id: int,
    job_id: int,
    output_format: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Generate and download the latest formatted CV for a candidate/job pair."""
    candidate, job = _candidate_and_job(db, candidate_id, job_id)
    selected_format = (output_format or load_settings().cv_format.output_format or "pdf").lower()
    if selected_format not in {"docx", "pdf"}:
        raise HTTPException(status_code=400, detail="output_format must be docx or pdf")
    formatter = CVFormatterAgent()
    file_path = formatter.generate_file(candidate, job, selected_format)
    file = Path(file_path)
    if not file.exists():
        raise HTTPException(status_code=500, detail="Formatted CV could not be created")

    cv_record = (
        db.query(CV)
        .filter(CV.candidate_id == candidate_id)
        .order_by(CV.created_at.desc())
        .first()
    )
    if cv_record:
        cv_record.formatted_cv_path = str(file)
        db.commit()

    media_type = (
        "application/pdf"
        if file.suffix.lower() == ".pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    return FileResponse(str(file), media_type=media_type, filename=file.name)


@router.post("/candidate/{candidate_id}/job/{job_id}/download-edited")
def download_edited_candidate_job_cv(
    candidate_id: int,
    job_id: int,
    payload: Dict[str, Any] = Body(default_factory=dict),
    output_format: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Generate and download a CV using edited content from the Change CV dialog."""
    candidate, job = _candidate_and_job(db, candidate_id, job_id)
    selected_format = (output_format or load_settings().cv_format.output_format or "pdf").lower()
    if selected_format not in {"docx", "pdf"}:
        raise HTTPException(status_code=400, detail="output_format must be docx or pdf")

    content_overrides = payload.get("content") if isinstance(payload.get("content"), dict) else payload
    formatter = CVFormatterAgent()
    file_path = formatter.generate_file(candidate, job, selected_format, content_overrides=content_overrides)
    file = Path(file_path)
    if not file.exists():
        raise HTTPException(status_code=500, detail="Formatted CV could not be created")

    cv_record = (
        db.query(CV)
        .filter(CV.candidate_id == candidate_id)
        .order_by(CV.created_at.desc())
        .first()
    )
    if cv_record:
        cv_record.formatted_cv_path = str(file)
        db.commit()

    media_type = (
        "application/pdf"
        if file.suffix.lower() == ".pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    return FileResponse(str(file), media_type=media_type, filename=file.name)


@router.get("/{cv_id}")
def get_cv(cv_id: int, db: Session = Depends(get_db)):
    """Get one CV record by ID."""
    cv = db.query(CV).filter(CV.id == cv_id).first()
    if not cv:
        raise HTTPException(status_code=404, detail="CV not found")
    return cv


def _save_upload(file: UploadFile, prefix: str = "") -> str:
    filename = Path(file.filename or "uploaded_cv").name
    _validate_upload(filename)
    file_path = UPLOAD_DIR / f"{prefix}{filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return str(file_path)


def _candidate_and_job(db: Session, candidate_id: int, job_id: int) -> tuple[Candidate, Job]:
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return candidate, job


def _validate_upload(filename: str) -> None:
    extension = Path(filename).suffix.lower().lstrip(".")
    accepted = {item.lower().lstrip(".") for item in load_settings().cv_format.accepted_uploads}
    if extension not in accepted:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported CV format. Accepted formats: {', '.join(sorted(accepted))}",
        )
