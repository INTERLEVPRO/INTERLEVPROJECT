from typing import Dict, Any
from backend.app.services.llm.base import LLMProvider
from backend.app.models.candidate import Candidate, CandidateSkill
from sqlalchemy.orm import Session
from datetime import datetime

class CandidateProfileAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def process_profile(self, db: Session, extracted_data: Dict[str, Any]) -> Candidate:
        """
        Converts extracted CV data into a clean INTERLEV candidate profile.
        """
        # Rule-based experience level
        exp_years = extracted_data.get("experience_years", 0)
        if exp_years >= 7:
            level = "Senior"
        elif exp_years >= 3:
            level = "Mid Level"
        else:
            level = "Junior"

        # Generate summary using LLM if not present
        summary = extracted_data.get("summary")
        if not summary:
            summary = self.llm.summarize(extracted_data.get("raw_text", ""))

        # Check for completeness
        is_complete = all([
            extracted_data.get("name"),
            extracted_data.get("email"),
            extracted_data.get("skills")
        ])
        status = "complete" if is_complete else "incomplete"

        email = extracted_data.get("email")
        candidate = None
        if email:
            candidate = db.query(Candidate).filter(Candidate.email == email).first()
        
        if candidate:
            # Update existing candidate
            candidate.name = extracted_data.get("name")
            candidate.phone = extracted_data.get("phone")
            candidate.location = extracted_data.get("location")
            candidate.summary = summary
            candidate.main_role = extracted_data.get("job_titles")[0] if extracted_data.get("job_titles") else candidate.main_role
            candidate.experience_years = exp_years
            candidate.experience_level = level
            candidate.profile_status = status
            candidate.updated_at = datetime.utcnow()
        else:
            # Create new Candidate record
            candidate = Candidate(
                name=extracted_data.get("name"),
                email=extracted_data.get("email"),
                phone=extracted_data.get("phone"),
                location=extracted_data.get("location"),
                summary=summary,
                main_role=extracted_data.get("job_titles")[0] if extracted_data.get("job_titles") else None,
                experience_years=exp_years,
                experience_level=level,
                profile_status=status
            )
            db.add(candidate)
        
        db.flush() # Get ID

        if candidate.id:
            db.query(CandidateSkill).filter(CandidateSkill.candidate_id == candidate.id).delete()

        # Add skills
        for skill_name in extracted_data.get("skills", []):
            skill = CandidateSkill(
                candidate_id=candidate.id,
                skill_name=skill_name
            )
            db.add(skill)

        db.commit()
        db.refresh(candidate)
        return candidate
