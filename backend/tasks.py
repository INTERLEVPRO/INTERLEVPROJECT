from backend.core.celery_app import celery_app
from backend.agents.orchestrator import run_orchestrator
import time

@celery_app.task(name="run_agentic_workflow", bind=True)
def run_agentic_workflow(self, cv_text: str, goal: str):
    """
    Celery task to run the full Agentic AI workflow.
    """
    self.update_state(state='PROGRESS', meta={'status': 'Agent is thinking...'})
    
    try:
        # Run the orchestrator
        result = run_orchestrator(goal, cv_text)
        
        # Return the final result
        return {"status": "COMPLETED", "result": result}
    except Exception as e:
        self.update_state(state='FAILURE', meta={'status': str(e)})
        return {"status": "FAILED", "error": str(e)}
