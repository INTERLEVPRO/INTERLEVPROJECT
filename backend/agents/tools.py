from typing import List, Dict, Any
import json
from backend.models.schemas import CandidateProfile, Project, MatchResult, ApplicationDraft
from backend.agents.cv_reader import parse_cv_with_ai
from backend.agents.search import search_freelance_projects
from backend.agents.matching import match_projects
from backend.agents.application import draft_application
from backend.core.config import settings

def get_tools_schema() -> List[Dict[str, Any]]:
    """Returns the tool definitions for OpenAI function calling."""
    return [
        {
            "type": "function",
            "function": {
                "name": "parse_cv",
                "description": "Extract structured information from raw CV text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "cv_text": {"type": "string", "description": "The full text content of the CV."}
                    },
                    "required": ["cv_text"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_projects",
                "description": "Search for freelance projects based on candidate skills.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skills": {"type": "array", "items": {"type": "string"}, "description": "List of technical skills to search for."}
                    },
                    "required": ["skills"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "match_projects",
                "description": "Score and explain why specific projects match a candidate profile.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "profile": {"type": "object", "description": "The parsed candidate profile."},
                        "projects": {"type": "array", "items": {"type": "object"}, "description": "List of projects to match."}
                    },
                    "required": ["profile", "projects"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "draft_application",
                "description": "Generate a professional email and message draft for a specific project.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "profile": {"type": "object", "description": "The candidate profile."},
                        "project": {"type": "object", "description": "The selected project."}
                    },
                    "required": ["profile", "project"]
                }
            }
        }
    ]

def tool_wrapper(name: str, args: Dict[str, Any]) -> str:
    """
    Executes the corresponding tool logic.
    If OPENAI_API_KEY is not set or is 'mock', returns mock data for testing.
    """
    is_mock = not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "mock"
    
    try:
        if name == "parse_cv":
            if is_mock:
                return json.dumps({
                    "name": "John Doe",
                    "role": "Senior Python Developer",
                    "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                    "experience_years": 8,
                    "languages": ["English", "German"],
                    "summary": "Experienced backend developer specializing in microservices."
                })
            profile = parse_cv_with_ai(args["cv_text"])
            return profile.model_dump_json()

        elif name == "search_projects":
            # Search logic is already mock-friendly in search.py
            projects = search_freelance_projects(args["skills"])
            return json.dumps([p.model_dump() for p in projects])

        elif name == "match_projects":
            if is_mock:
                # Mock matching logic
                profile_data = args["profile"]
                projects_data = args["projects"]
                results = []
                for p in projects_data:
                    results.append({
                        "project": p,
                        "match_score": 85 if "Python" in p["required_skills"] else 40,
                        "reason": "Strong match in core backend skills." if "Python" in p["required_skills"] else "Limited skill overlap."
                    })
                return json.dumps(results)
            
            profile = CandidateProfile(**args["profile"])
            projects = [Project(**p) for p in args["projects"]]
            matches = match_projects(profile, projects)
            return json.dumps([m.model_dump() for m in matches])

        elif name == "draft_application":
            if is_mock:
                return json.dumps({
                    "project_id": args["project"]["id"],
                    "email_subject": f"Application for {args['project']['title']}",
                    "email_body": "Dear Hiring Manager,\n\nI am excited to apply...",
                    "portal_message": "Hi, I'm interested in this project!"
                })
            
            profile = CandidateProfile(**args["profile"])
            project = Project(**args["project"])
            draft = draft_application(profile, project)
            return draft.model_dump_json()

    except Exception as e:
        return json.dumps({"error": str(e)})

    return json.dumps({"error": f"Tool {name} not found"})
