from openai import OpenAI
from backend.core.config import settings
from backend.models.schemas import CandidateProfile, Project, ApplicationDraft

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def draft_application(profile: CandidateProfile, project: Project) -> ApplicationDraft:
    prompt = f"""
    You are an expert recruiter writing a highly professional, persuasive application for a freelance project.
    
    Candidate Profile:
    Name: {profile.name or "The candidate"}
    Role: {profile.role}
    Experience: {profile.experience_years} years
    Skills: {', '.join(profile.skills)}
    
    Project:
    Title: {project.title}
    Required Skills: {', '.join(project.required_skills)}
    Portal: {project.portal_source}
    
    Please provide an email draft with:
    1. A catchy subject line.
    2. A professional email body explaining why the candidate is a perfect fit based on their skills and the project requirements.
    3. A shorter, punchy message suitable for a direct message on the freelance portal ({project.portal_source}).
    
    Return the response as a JSON object with keys:
    - email_subject
    - email_body
    - portal_message
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a professional recruiting assistant."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        import json
        result_data = json.loads(response.choices[0].message.content)
        
        return ApplicationDraft(
            project_id=project.id,
            email_subject=result_data.get("email_subject", "Application for Freelance Project"),
            email_body=result_data.get("email_body", "Please find my CV attached."),
            portal_message=result_data.get("portal_message", "I am interested in your project.")
        )
    except Exception as e:
        print(f"Error drafting application: {e}")
        return ApplicationDraft(
            project_id=project.id,
            email_subject="Application: " + project.title,
            email_body="Error generating email body.",
            portal_message="Error generating message."
        )
