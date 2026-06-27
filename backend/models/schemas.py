from pydantic import BaseModel, Field
from typing import List, Optional

class CandidateProfile(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    experience_years: Optional[int] = None
    languages: List[str] = Field(default_factory=list)
    summary: Optional[str] = None

class Project(BaseModel):
    id: str
    title: str
    description: str
    required_skills: List[str]
    portal_source: str
    url: Optional[str] = None

class MatchResult(BaseModel):
    project: Project
    match_score: int
    reason: str

class ApplicationDraft(BaseModel):
    project_id: str
    email_subject: str
    email_body: str
    portal_message: str
