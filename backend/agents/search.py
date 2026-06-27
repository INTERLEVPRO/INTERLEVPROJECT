import uuid
from typing import List
from backend.models.schemas import Project

# Mock database of freelance projects
MOCK_PROJECTS = [
    {
        "id": "proj-002",
        "title": "Senior Python Backend Developer",
        "description": "We need a Senior Python Developer with FastAPI and PostgreSQL experience to build scalable microservices.",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Microservices", "Docker"],
        "portal_source": "Hays",
        "url": "https://www.hays.de/projects/002"
    },
    {
        "id": "proj-003",
        "title": "Frontend React Engineer",
        "description": "Seeking a frontend developer skilled in React, TypeScript, and state management for a 6-month contract.",
        "required_skills": ["React", "TypeScript", "Redux", "Frontend Development"],
        "portal_source": "Freelancer.de",
        "url": "https://www.freelancer.de/projects/003"
    },
    {
        "id": "proj-004",
        "title": "Data Scientist - AI & ML",
        "description": "Data Scientist needed for predictive modeling and NLP tasks. Experience with OpenAI API is a plus.",
        "required_skills": ["Python", "Machine Learning", "NLP", "OpenAI API", "Pandas"],
        "portal_source": "Gulp",
        "url": "https://www.gulp.de/projects/004"
    }
]

def search_freelance_projects(skills: List[str]) -> List[Project]:
    """
    Simulates searching freelance portals based on candidate skills.
    In a real scenario, this would use Playwright to scrape portals like Hays, Gulp, etc.
    For this MVP, we return a mock list of projects to demonstrate matching.
    """
    
    # We could filter the mock list based on skills, but we will return all 
    # to allow the Matching Agent to score them and demonstrate good vs bad matches.
    
    projects = []
    for p in MOCK_PROJECTS:
        projects.append(Project(**p))
        
    return projects
