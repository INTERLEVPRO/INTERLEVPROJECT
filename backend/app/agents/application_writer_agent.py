from typing import Dict, Any
from backend.app.services.llm.base import LLMProvider
from backend.app.models.candidate import Candidate
from backend.app.models.job import Job

class ApplicationWriterAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def draft_application(self, candidate: Candidate, job: Job, match_score: float) -> Dict[str, Any]:
        """
        Prepare proposal/email for selected job and candidate.
        Uses match score to determine confidence level.
        """
        confidence = "normal"
        if match_score >= 85:
            confidence = "confident"
        elif match_score < 70:
            confidence = "requires_review"

        skills = ", ".join([skill.skill_name for skill in candidate.skills]) or "not listed"
        prompt = f"""
        Generate a professional job application proposal.
        CANDIDATE: {candidate.name}, Role: {candidate.main_role}, Skills: {skills}
        JOB: {job.title} at {job.company}
        JOB DESCRIPTION: {job.description or ""}
        MATCH SCORE: {match_score}%
        CONFIDENCE: {confidence}

        Return a JSON object with: email_subject, email_body, portal_message.
        """

        try:
            draft = self.llm.extract_json(prompt)
        except Exception:
            draft = {}

        return self._normalize_draft(draft, candidate, job, match_score, confidence)

    def _normalize_draft(
        self,
        draft: Dict[str, Any],
        candidate: Candidate,
        job: Job,
        match_score: float,
        confidence: str,
    ) -> Dict[str, Any]:
        fallback = self._fallback_draft(candidate, job, match_score, confidence)
        normalized = {
            "email_subject": draft.get("email_subject") or fallback["email_subject"],
            "email_body": draft.get("email_body") or fallback["email_body"],
            "portal_message": draft.get("portal_message") or fallback["portal_message"],
            "confidence": draft.get("confidence") or confidence,
        }
        return normalized

    def _fallback_draft(
        self,
        candidate: Candidate,
        job: Job,
        match_score: float,
        confidence: str,
    ) -> Dict[str, str]:
        role = candidate.main_role or "consultant"
        company = job.company or "your team"
        title = job.title or "the role"
        skills = ", ".join([skill.skill_name for skill in candidate.skills[:6]]) or "relevant delivery skills"

        body = (
            f"Hi {company} team,\n\n"
            f"I am applying for {title}. {candidate.name} is a {role} with experience in {skills}. "
            f"The current INTERLEV match score is {round(match_score, 2)}%, which indicates a {confidence} fit for the role.\n\n"
            "I would be happy to discuss availability, project scope, and delivery timelines.\n\n"
            "Best regards,\n"
            f"{candidate.name}"
        )
        portal_message = (
            f"{candidate.name} is a strong fit for {title}, with hands-on experience in {skills}. "
            f"INTERLEV scored this profile at {round(match_score, 2)}% for the listed requirements."
        )
        return {
            "email_subject": f"Application for {title} - {candidate.name}",
            "email_body": body,
            "portal_message": portal_message,
            "confidence": confidence,
        }
