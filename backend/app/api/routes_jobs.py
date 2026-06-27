from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app.agents.job_search_agent import JobSearchAgent
from backend.app.models.job import Job
from backend.app.tasks.job_tasks import keyword_search_workflow_task, search_matching_candidates_task
from pydantic import BaseModel

router = APIRouter()

class KeywordSearchRequest(BaseModel):
    keywords: List[str]
    candidate_id: Optional[int] = None
    source_keys: Optional[List[str]] = None
    source_url: Optional[str] = None
    search_mode: str = "real_search"

class JobMatchRequest(BaseModel):
    job_id: int

@router.post("/search-by-keywords")
def search_jobs(request: KeywordSearchRequest):
    """Start a background search for jobs based on keywords."""
    clean_search_mode = (request.search_mode or "real_search").strip().lower()
    if clean_search_mode not in {"real_search", "fast_pass"}:
        raise HTTPException(status_code=400, detail="search_mode must be real_search or fast_pass")
    try:
        if clean_search_mode != "fast_pass":
            JobSearchAgent().validate_source_url(request.source_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    task = keyword_search_workflow_task.delay(
        request.keywords,
        request.candidate_id,
        request.source_keys,
        request.source_url,
        clean_search_mode,
    )
    return {"message": "Job search started", "task_id": task.id}

@router.post("/find-candidates")
def find_candidates(request: JobMatchRequest):
    """Start a background matching task to find candidates for a specific job."""
    task = search_matching_candidates_task.delay(request.job_id)
    return {"message": "Candidate matching started", "task_id": task.id}

@router.get("/")
def get_jobs(db: Session = Depends(get_db)):
    """List all jobs in the database."""
    return db.query(Job).all()

@router.get("/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get details of a specific job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
