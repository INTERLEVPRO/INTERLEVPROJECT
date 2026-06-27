from pathlib import Path
import re

import pdfplumber
import docx
from typing import Dict, Any, Optional
from backend.app.services.llm.base import LLMProvider

COMMON_SKILLS = [
    "Python",
    "FastAPI",
    "Django",
    "Flask",
    "Java",
    "C++",
    "C#",
    "React",
    "Angular",
    "Vue.js",
    "HTML",
    "CSS",
    "Next.js",
    "JavaScript",
    "TypeScript",
    "SQL",
    "SQL Server",
    "PostgreSQL",
    "MySQL",
    ".NET",
    "ASP.NET",
    "Docker",
    "Kubernetes",
    "AWS",
    "Azure",
    "GCP",
    "Redis",
    "Celery",
    "Git",
    "REST API",
    "API Integration",
    "GraphQL",
    "Microsoft 365",
    "Office 365",
    "Outlook",
    "Calendar",
    "QA",
    "Testing",
    "Customer Service",
    "Marketing",
    "Software Engineering",
]

class CVReaderAgent:
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    def read_cv(self, file_path: str) -> Dict[str, Any]:
        """
        Main entry point for reading a CV.
        Decides which parser to use based on extension.
        """
        text = ""
        extension = Path(file_path).suffix.lower()
        if extension == ".pdf":
            text = self._parse_pdf(file_path)
        elif extension == ".docx":
            text = self._parse_docx(file_path)
        elif extension in {".txt", ".md", ".markdown"}:
            text = self._parse_txt(file_path)
        else:
            raise ValueError("Unsupported file format. Upload PDF, DOCX, TXT, or MD.")

        if not text.strip():
            # In a real scenario, we would trigger OCR here
            return {"error": "Could not extract text from file", "status": "failed"}

        structured_data = self._extract_structured_data(text)
        
        # Calculate confidence (mock for now)
        confidence = 0.95 if structured_data.get("email") and structured_data.get("name") else 0.6
        structured_data["parse_confidence"] = confidence
        structured_data["raw_text"] = text

        return structured_data

    def _parse_pdf(self, file_path: str) -> str:
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        return text

    def _parse_docx(self, file_path: str) -> str:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def _parse_txt(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def _extract_structured_data(self, text: str) -> Dict[str, Any]:
        prompt = f"""
        Extract structured information from the following CV text. 
        Return a JSON object with: name, email, phone, skills (list), experience_years (int), 
        education, job_titles (list), location, languages (list), certifications (list).
        
        CV TEXT:
        {text}
        """
        try:
            extracted = self.llm.extract_json(prompt)
            if extracted.get("error"):
                return self._fallback_structured_data(text)
            fallback = self._fallback_structured_data(text)
            extracted["skills"] = self._merge_skills(extracted.get("skills", []), fallback.get("skills", []))
            for key in ("name", "email", "phone", "location", "summary"):
                if not extracted.get(key) and fallback.get(key):
                    extracted[key] = fallback[key]
            return extracted
        except Exception:
            return self._fallback_structured_data(text)

    def _fallback_structured_data(self, text: str) -> Dict[str, Any]:
        lines = [line.strip("#- *\t ") for line in text.splitlines() if line.strip()]
        email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
        phone_match = re.search(r"(\+?\d[\d\s().-]{7,}\d)", text)
        years_match = re.search(r"(\d+)\+?\s*(?:years|yrs)", text, re.IGNORECASE)
        skills = [skill for skill in COMMON_SKILLS if self._contains_skill(text, skill)]
        name = self._fallback_name(lines, email_match.group(0) if email_match else "")
        role = self._fallback_role(lines)

        return {
            "name": name,
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(1).strip() if phone_match else "",
            "location": self._fallback_location(lines),
            "skills": skills or ["General"],
            "experience_years": int(years_match.group(1)) if years_match else 0,
            "education": "",
            "job_titles": [role] if role else [],
            "languages": [],
            "certifications": [],
            "summary": self._fallback_summary(text),
        }

    def _fallback_name(self, lines, email: str) -> str:
        for line in lines[:8]:
            if "@" in line or len(line) > 80:
                continue
            if re.search(r"\d", line):
                continue
            if any(word in line.lower() for word in ("cv", "resume", "profile", "curriculum")):
                continue
            return line
        return email.split("@")[0].replace(".", " ").title() if email else "Uploaded Candidate"

    def _fallback_role(self, lines) -> str:
        role_markers = ("developer", "engineer", "consultant", "manager", "designer", "analyst", "architect")
        for line in lines[:20]:
            if any(marker in line.lower() for marker in role_markers):
                return line[:120]
        return ""

    def _fallback_location(self, lines) -> str:
        for line in lines[:20]:
            lower = line.lower()
            if lower.startswith("location"):
                return line.split(":", 1)[-1].strip()
        return ""

    def _fallback_summary(self, text: str) -> str:
        clean = " ".join(text.split())
        return clean[:500]

    def _contains_skill(self, text: str, skill: str) -> bool:
        if skill in {"C++", "C#", ".NET"}:
            return skill.lower() in text.lower()
        return bool(re.search(rf"\b{re.escape(skill)}\b", text, re.IGNORECASE))

    def _merge_skills(self, primary: Any, fallback: Any) -> list[str]:
        merged = []
        for source in (primary or [], fallback or []):
            if not isinstance(source, str):
                continue
            skill = source.strip()
            if skill and skill.lower() not in {item.lower() for item in merged}:
                merged.append(skill)
        return merged or ["General"]
