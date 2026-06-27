import re
from typing import Dict, Any, List

from backend.app.models.candidate import Candidate
from backend.app.models.job import Job


SKILL_ALIASES = {
    "python": ["python"],
    "fastapi": ["fastapi", "fast api"],
    "django": ["django"],
    "flask": ["flask"],
    "java": ["java"],
    "c++": ["c++"],
    "c#": ["c#"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "javascript": ["javascript", "java script"],
    "typescript": ["typescript", "type script"],
    "react": ["react", "react.js", "reactjs"],
    "angular": ["angular", "angular.js"],
    "vue.js": ["vue", "vue.js", "vuejs"],
    "next.js": ["next.js", "nextjs"],
    ".net": [".net", "dotnet", "asp.net"],
    "sql": ["sql", "sql server", "mysql", "postgresql", "database queries"],
    "docker": ["docker"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services"],
    "azure": ["azure"],
    "gcp": ["gcp", "google cloud"],
    "redis": ["redis"],
    "celery": ["celery"],
    "git": ["git", "github", "gitlab"],
    "rest api": ["rest api", "restful api", "api integration"],
    "graphql": ["graphql", "graph ql"],
    "microsoft 365": ["microsoft 365", "office 365", "m365", "o365"],
    "outlook": ["outlook"],
    "calendar": ["calendar"],
    "qa": ["qa", "quality assurance", "testing"],
    "customer service": ["customer service", "customer support"],
    "marketing": ["marketing", "digital marketing"],
    "software engineering": ["software engineering", "software development", "computer science"],
}


class MatchingAgent:
    def calculate_match(self, candidate: Candidate, job: Job) -> Dict[str, Any]:
        """
        Compare candidate profile with job requirements using CV-backed local logic.
        """
        score = 0.0
        candidate_text = self._candidate_text(candidate)
        job_text = self._job_text(job)

        candidate_skills = self._candidate_skills(candidate, candidate_text)
        required_skills = self._job_required_skills(job, job_text)
        nice_to_have_skills = self._canonical_skill_list(job.nice_to_have_skills or [])

        if required_skills:
            matched_skills = [skill for skill in required_skills if skill in candidate_skills]
            missing_skills = [skill for skill in required_skills if skill not in candidate_skills]
            skill_ratio = len(matched_skills) / len(required_skills)
            score += skill_ratio * 65
            score += self._cv_evidence_bonus(matched_skills, required_skills, candidate_text)
        else:
            matched_skills = []
            missing_skills = []
            score += 20 if candidate_skills else 0

        if nice_to_have_skills:
            nice_matches = [skill for skill in nice_to_have_skills if skill in candidate_skills]
            score += (len(nice_matches) / len(nice_to_have_skills)) * 10

        score += self._role_score(candidate, candidate_text, job_text)
        score += self._experience_score(candidate, job_text)
        score += self._location_score(candidate, job)
        score = min(score, 100)

        match_level = "Poor Match"
        if score >= 90:
            match_level = "Strong Match"
        elif score >= 75:
            match_level = "Good Match"
        elif score >= 60:
            match_level = "Possible Match"

        if required_skills:
            reason = (
                f"CV matched {len(matched_skills)} of {len(required_skills)} required skills "
                f"({', '.join(matched_skills) or 'none'}). Experience level: {candidate.experience_level}."
            )
        else:
            reason = f"No clear job skill requirements were found. Experience level: {candidate.experience_level}."

        return {
            "match_percentage": round(score, 2),
            "match_level": match_level,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "reason": reason,
        }

    def _candidate_text(self, candidate: Candidate) -> str:
        cv_text = ""
        cvs = list(getattr(candidate, "cvs", []) or [])
        if cvs:
            latest_cv = sorted(cvs, key=lambda cv: str(getattr(cv, "created_at", "") or ""), reverse=True)[0]
            cv_text = getattr(latest_cv, "parsed_text", "") or ""
        return " ".join(
            str(part or "")
            for part in (
                candidate.main_role,
                candidate.summary,
                candidate.experience_level,
                cv_text,
            )
        )

    def _job_text(self, job: Job) -> str:
        return " ".join(
            str(part or "")
            for part in (
                job.title,
                job.company,
                job.platform,
                job.description,
                " ".join(job.required_skills or []),
                " ".join(job.nice_to_have_skills or []),
            )
        )

    def _candidate_skills(self, candidate: Candidate, candidate_text: str) -> List[str]:
        stored = [skill.skill_name for skill in getattr(candidate, "skills", []) if skill.skill_name]
        return self._ordered_unique(self._canonical_skill_list(stored) + self._skills_from_text(candidate_text))

    def _job_required_skills(self, job: Job, job_text: str) -> List[str]:
        explicit = self._canonical_skill_list(job.required_skills or [])
        inferred = self._skills_from_text(self._focused_job_text(job_text))
        return self._ordered_unique(explicit + inferred)

    def _focused_job_text(self, job_text: str) -> str:
        return job_text[:3500]

    def _canonical_skill_list(self, skills: List[Any]) -> List[str]:
        return self._ordered_unique(
            canonical
            for skill in skills
            if (canonical := self._canonical_skill(str(skill)))
        )

    def _skills_from_text(self, text: str) -> List[str]:
        return [canonical for canonical, aliases in SKILL_ALIASES.items() if self._contains_any(text, aliases)]

    def _canonical_skill(self, value: str) -> str:
        normalized = self._normalize(value)
        for canonical, aliases in SKILL_ALIASES.items():
            if normalized == canonical or normalized in {self._normalize(alias) for alias in aliases}:
                return canonical
        return normalized

    def _contains_any(self, text: str, aliases: List[str]) -> bool:
        return any(self._contains_term(text, alias) for alias in aliases)

    def _contains_term(self, text: str, term: str) -> bool:
        lower = text.lower()
        if term in {"c++", "c#", ".net"}:
            return term in lower
        return bool(re.search(rf"\b{re.escape(term.lower())}\b", lower))

    def _normalize(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.strip().lower())

    def _ordered_unique(self, values) -> List[str]:
        result = []
        seen = set()
        for value in values:
            if value and value not in seen:
                result.append(value)
                seen.add(value)
        return result

    def _cv_evidence_bonus(self, matched_skills: List[str], required_skills: List[str], candidate_text: str) -> float:
        if not matched_skills or len(matched_skills) != len(required_skills):
            return 0.0
        cv_backed = [
            skill for skill in matched_skills
            if self._contains_any(candidate_text, SKILL_ALIASES.get(skill, [skill]))
        ]
        if len(required_skills) >= 3 and len(cv_backed) == len(required_skills):
            return 10.0
        if len(required_skills) == 2 and len(cv_backed) == 2:
            return 6.0
        if len(required_skills) == 1 and cv_backed:
            return 4.0
        return 0.0

    def _role_score(self, candidate: Candidate, candidate_text: str, job_text: str) -> float:
        role_terms = [
            "developer",
            "engineer",
            "software",
            "frontend",
            "backend",
            "full stack",
            "qa",
            "testing",
            "support",
            "marketing",
            "customer",
        ]
        candidate_terms = [term for term in role_terms if self._contains_term(candidate_text, term)]
        job_terms = [term for term in role_terms if self._contains_term(job_text, term)]
        if set(candidate_terms) & set(job_terms):
            return 10.0
        if candidate.main_role and self._contains_term(job_text, candidate.main_role.lower()):
            return 10.0
        return 0.0

    def _experience_score(self, candidate: Candidate, job_text: str) -> float:
        level = (candidate.experience_level or "").lower()
        if any(term in job_text.lower() for term in ("senior", "lead", "architect")):
            return 10.0 if level == "senior" else 4.0 if level == "mid level" else 0.0
        if any(term in job_text.lower() for term in ("junior", "intern", "entry level", "trainee")):
            return 10.0 if level == "junior" else 8.0 if level == "mid level" else 5.0
        if level == "senior":
            return 10.0
        if level == "mid level":
            return 8.0
        return 6.0

    def _location_score(self, candidate: Candidate, job: Job) -> float:
        contract_type = (job.contract_type or "").lower()
        job_location = (job.location or "").lower()
        candidate_location = (candidate.location or "").lower()
        if "remote" in contract_type or "remote" in job_location:
            return 5.0
        if candidate_location and job_location and candidate_location == job_location:
            return 5.0
        return 0.0
