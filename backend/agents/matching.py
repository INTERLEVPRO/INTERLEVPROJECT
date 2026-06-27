import json
from typing import List
from openai import OpenAI
from backend.core.config import settings
from backend.models.schemas import CandidateProfile, Project, MatchResult

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def match_projects(profile: CandidateProfile, projects: List[Project]) -> List[MatchResult]:
    match_results = []
    
    # In a real app, you might do this in a single batch call or with parallel execution
    for project in projects:
        prompt = f"""
        You are an expert technical recruiter matching a candidate to a freelance project.
        Compare the candidate's profile with the project requirements.
        
        Candidate Profile:
        Role: {profile.role}
        Skills: {', '.join(profile.skills)}
        Experience: {profile.experience_years} years
        Languages: {', '.join(profile.languages)}
        
        Project:
        Title: {project.title}
        Required Skills: {', '.join(project.required_skills)}
        Description: {project.description}
        
        Return a JSON object with two keys:
        - match_score: An integer from 0 to 100 representing how well the candidate fits the project.
        - reason: A brief explanation (1-2 sentences) of why they got this score, highlighting key matching or missing skills.
        """
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI matching agent."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result_data = json.loads(response.choices[0].message.content)
            
            match_results.append(MatchResult(
                project=project,
                match_score=result_data.get("match_score", 0),
                reason=result_data.get("reason", "No reason provided")
            ))
            
        except Exception as e:
            print(f"Error matching project {project.id}: {e}")
            # Add a fallback score in case of error
            match_results.append(MatchResult(
                project=project,
                match_score=0,
                reason="Error calculating match score."
            ))
            
    # Sort results by match_score descending
    match_results.sort(key=lambda x: x.match_score, reverse=True)
    return match_results
