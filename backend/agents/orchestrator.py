import json
from openai import OpenAI
from backend.core.config import settings
from backend.agents.tools import get_tools_schema, tool_wrapper

def run_orchestrator(goal: str, cv_text: str = None) -> str:
    """
    Main orchestrator loop that uses tools to achieve a goal.
    Goal Example: 'Find the best matching freelance project for my CV and draft an application.'
    """
    
    is_mock = not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "mock"
    
    if is_mock:
        # Simulate the agentic flow for demonstration/testing
        print("DEBUG: Running in MOCK mode")
        profile_json = tool_wrapper("parse_cv", {"cv_text": cv_text or "Mock CV Text"})
        profile = json.loads(profile_json)
        
        projects_json = tool_wrapper("search_projects", {"skills": profile["skills"]})
        projects = json.loads(projects_json)
        
        matches_json = tool_wrapper("match_projects", {"profile": profile, "projects": projects})
        matches = json.loads(matches_json)
        
        best_match = matches[0] if matches else None
        if not best_match:
            return "No matching projects found."
            
        draft_json = tool_wrapper("draft_application", {"profile": profile, "project": best_match["project"]})
        return draft_json

    # Real Agentic Loop with OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    system_prompt = """
    You are an autonomous INTERLEV Freelancer Matching Agent.
    Your goal is to help the user find the best freelance project and prepare a high-quality application.
    
    You have access to tools to:
    1. parse_cv: Get structured data from raw text.
    2. search_projects: Find open freelance roles.
    3. match_projects: Evaluate how well a candidate fits certain roles.
    4. draft_application: Create professional application messages.
    
    Process:
    - If you have raw CV text, parse it first.
    - Use the skills from the profile to search for projects.
    - Match the projects against the profile to find the best fit.
    - Once you have the best match, draft the application.
    - Return the final application draft as the final answer.
    """
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"{goal}\n\nCV Text: {cv_text if cv_text else 'No CV provided yet.'}"}
    ]
    
    tools = get_tools_schema()
    
    # Simple loop for up to 10 steps
    for _ in range(10):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        messages.append(message)
        
        if not message.tool_calls:
            return message.content
            
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            print(f"DEBUG: Agent calling tool: {tool_name}")
            tool_result = tool_wrapper(tool_name, tool_args)
            
            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": tool_name,
                "content": tool_result
            })
            
    return "Agent exceeded maximum steps."
