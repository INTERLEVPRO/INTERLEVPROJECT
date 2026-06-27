import json
from typing import Dict, Any, Optional
from backend.app.services.llm.base import LLMProvider

class MockLLMProvider(LLMProvider):
    def extract_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Returns mock structured data based on keywords in prompt."""
        if "application proposal" in prompt or "portal_message" in prompt:
            return {
                "email_subject": "Application for Senior Python Developer",
                "email_body": (
                    "Hi team,\n\n"
                    "I am applying for this role through INTERLEV. My background aligns strongly "
                    "with the listed backend, API, and delivery requirements.\n\n"
                    "Best regards"
                ),
                "portal_message": "INTERLEV draft proposal generated in demo mode.",
                "confidence": "normal",
            }
        if "CV" in prompt or "cv" in prompt:
            import random
            rand_id = random.randint(100, 999)
            return {
                "name": f"Test Candidate {rand_id}",
                "email": f"candidate{rand_id}@example.com",
                "phone": f"+49 151 {rand_id}4567",
                "location": "Berlin, Germany",
                "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
                "experience_years": 8,
                "education": "MSc in Computer Science",
                "job_titles": ["Senior Backend Developer", "Python Engineer"],
                "languages": ["English", "German"],
                "certifications": ["AWS Solutions Architect"]
            }
        elif "job" in prompt or "Job" in prompt:
            return {
                "title": "Senior Python Developer",
                "required_skills": ["Python", "FastAPI", "SQL"],
                "nice_to_have_skills": ["Kubernetes", "Redis"],
                "experience_required": 5,
                "budget": "90-110k EUR",
                "location": "Remote",
                "contract_type": "Freelance"
            }
        return {"message": "Mock data not found for this prompt"}

    def generate_text(self, prompt: str) -> str:
        return f"Mock response for prompt: {prompt[:50]}..."

    def summarize(self, text: str) -> str:
        return f"Mock summary: This text is about {text[:30]}."


class UnavailableLLMProvider(LLMProvider):
    def __init__(self, reason: str):
        self.reason = reason

    def extract_json(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        raise RuntimeError(self.reason)

    def generate_text(self, prompt: str) -> str:
        raise RuntimeError(self.reason)

    def summarize(self, text: str) -> str:
        raise RuntimeError(self.reason)
