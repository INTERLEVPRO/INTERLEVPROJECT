from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.candidate import Candidate
from backend.app.models.job import Job
from backend.app.models.match import Match
from backend.app.agents.matching_agent import MatchingAgent
from backend.app.services.app_settings import load_settings
from pydantic import BaseModel

router = APIRouter()

class ManualMatchRequest(BaseModel):
    candidate_id: int
    job_id: int

@router.post("/run")
def run_manual_match(request: ManualMatchRequest, db: Session = Depends(get_db)):
    """Manually run the matching agent for a specific candidate and job."""
    candidate = db.query(Candidate).filter(Candidate.id == request.candidate_id).first()
    job = db.query(Job).filter(Job.id == request.job_id).first()
    
    if not candidate or not job:
        raise HTTPException(status_code=404, detail="Candidate or Job not found")
        
    matcher = MatchingAgent()
    match_data = matcher.calculate_match(candidate, job)
    threshold = max(50, int(load_settings().automation.min_match_score or 50))
    if match_data["match_percentage"] < threshold:
        raise HTTPException(status_code=400, detail=f"Match score is below {threshold}%")
    
    match_record = db.query(Match).filter(
        Match.candidate_id == candidate.id,
        Match.job_id == job.id,
    ).first()
    if match_record:
        match_record.match_percentage = match_data["match_percentage"]
        match_record.match_level = match_data["match_level"]
        match_record.matched_skills = match_data["matched_skills"]
        match_record.missing_skills = match_data["missing_skills"]
        match_record.reason = match_data["reason"]
    else:
        match_record = Match(
            candidate_id=candidate.id,
            job_id=job.id,
            match_percentage=match_data["match_percentage"],
            match_level=match_data["match_level"],
            matched_skills=match_data["matched_skills"],
            missing_skills=match_data["missing_skills"],
            reason=match_data["reason"]
        )
        db.add(match_record)
    db.commit()
    db.refresh(match_record)
    
    return match_record
