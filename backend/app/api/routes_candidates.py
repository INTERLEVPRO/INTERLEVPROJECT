from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.database import get_db
from backend.app.models.candidate import Candidate
from backend.app.models.match import Match
from backend.app.services.app_settings import load_settings
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class CandidateOut(BaseModel):
    id: int
    name: str
    email: str
    main_role: Optional[str] = None
    experience_years: int
    experience_level: str
    profile_status: str
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[CandidateOut])
def get_candidates(db: Session = Depends(get_db)):
    """List all candidates."""
    return db.query(Candidate).all()

@router.get("/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Get candidate details."""
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.get("/{candidate_id}/matches")
def get_candidate_matches(
    candidate_id: int,
    include_below_threshold: bool = False,
    db: Session = Depends(get_db),
):
    """Get candidate matches that respect the configured minimum score."""
    query = db.query(Match).filter(Match.candidate_id == candidate_id)
    if not include_below_threshold:
        threshold = max(50, int(load_settings().automation.min_match_score or 50))
        query = query.filter(Match.match_percentage >= threshold)
    return query.order_by(Match.match_percentage.desc(), Match.created_at.desc()).all()
