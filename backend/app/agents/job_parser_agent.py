from typing import Dict, Any
from backend.app.services.llm.base import LLMProvider
from backend.app.models.job import Job
from sqlalchemy.orm import Session

class JobParserAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def parse_job_description(self, db: Session, job: Job) -> Job:
        """
        Parses raw job description into structured fields using LLM fallback.
        """
        if not job.description:
            return job

        prompt = f"""
        Extract structured information from the following job description.
        Return a JSON object with: title, required_skills (list), nice_to_have_skills (list), 
        experience_required (int), budget, location, contract_type, language.
        
        JOB DESCRIPTION:
        {job.description}
        """
        
        extracted = self.llm.extract_json(prompt)
        
        # Update job fields if they were extracted and empty
        if extracted.get("required_skills"):
            job.required_skills = extracted["required_skills"]
        if extracted.get("nice_to_have_skills"):
            job.nice_to_have_skills = extracted["nice_to_have_skills"]
        if extracted.get("budget"):
            job.budget = extracted["budget"]
        if extracted.get("location"):
            job.location = extracted["location"]
            
        db.commit()
        return job
