from backend.app.tasks.celery_app import celery_app
from backend.app.database import SessionLocal
from backend.app.agents.cv_reader_agent import CVReaderAgent
from backend.app.agents.candidate_profile_agent import CandidateProfileAgent
from backend.app.services.llm.factory import get_llm_provider
from backend.app.models.cv import CV
from backend.app.agents.logging_agent import LoggingAgent
from backend.app.agents.notification_agent import NotificationAgent
from backend.app.services.app_settings import load_settings
from backend.app.tasks.celery_app import use_sync_tasks

FALLBACK_KEYWORDS = ["Python", "FastAPI", "Backend"]

@celery_app.task(name="parse_cv_task")
def parse_cv_task(file_path: str):
    db = SessionLocal()
    llm = get_llm_provider()
    
    reader = CVReaderAgent(llm)
    profiler = CandidateProfileAgent(llm)
    
    try:
        # 1. Read CV
        LoggingAgent.log_action(db, "CV Reader", "Reading file", "working", input_data={"path": file_path})
        extracted_data = reader.read_cv(file_path)
        if extracted_data.get("status") == "failed" or extracted_data.get("error"):
            error_message = extracted_data.get("error", "CV parsing failed")
            LoggingAgent.log_action(db, "CV Reader", "Reading file", "error", error_message=error_message)
            NotificationAgent.notify(db, "CV analysis failed", error_message, "error", "cv", {"path": file_path})
            return {"status": "error", "message": error_message}
        LoggingAgent.log_action(db, "CV Reader", "Reading file", "success", output_data=extracted_data)
        NotificationAgent.notify(
            db,
            "CV analyzed",
            f"Extracted profile data for {extracted_data.get('name', 'candidate')}.",
            "success",
            "cv",
            {"path": file_path, "skills": extracted_data.get("skills", [])},
        )
        
        # 2. Save CV record
        LoggingAgent.log_action(db, "Profiler", "Creating Profile", "working")
        cv_record = CV(
            original_file_path=file_path,
            parsed_text=extracted_data.get("raw_text"),
            parse_confidence=extracted_data.get("parse_confidence"),
            status="parsed"
        )
        db.add(cv_record)
        db.flush()
        
        # 3. Create Candidate Profile
        candidate = profiler.process_profile(db, extracted_data)
        LoggingAgent.log_action(db, "Profiler", "Creating Profile", "success", output_data={"candidate_id": candidate.id})
        NotificationAgent.notify(
            db,
            "Profile created",
            f"{candidate.name} is ready for job matching.",
            "success",
            "candidate",
            {"candidate_id": candidate.id},
        )
        
        # Update CV with candidate ID
        cv_record.candidate_id = candidate.id
        db.commit()
        
        # 4. Continue to matching (trigger next task)
        # match_jobs_for_candidate_task.delay(candidate.id)
        
        return {"status": "success", "candidate_id": candidate.id}
    except Exception as e:
        db.rollback()
        LoggingAgent.log_action(db, "System", "Task Failure", "error", error_message=str(e))
        NotificationAgent.notify(db, "Campaign error", str(e), "error", "system", {"path": file_path})
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(name="run_full_recruitment_workflow")
def run_full_recruitment_workflow(
    file_path: str,
    keywords=None,
    source_url: str | None = None,
    search_mode: str = "real_search",
):
    """
    ONE BUTTON TO RUN THEM ALL:
    Executes the entire multi-agent pipeline from CV upload to application drafting.
    """
    from backend.app.tasks.job_tasks import keyword_search_workflow_task
    from backend.app.tasks.formatting_tasks import format_cv_task
    
    # We chain the tasks together
    # Note: In a real scenario, we would pass IDs between tasks
    # For MVP, we'll run them sequentially using a wrapper or simple chain
    
    # 1. Parse CV (returns candidate_id)
    # 2. Format CV
    # 3. Search & Match Jobs (using extracted skills)
    
    # For the 'One Button' experience, we'll run the core steps sequentially
    # to ensure each agent has the data from the previous one.
    
    # 1. Parse CV (CandidateProfileAgent)
    result = parse_cv_task(file_path)
    
    if result["status"] == "success":
        candidate_id = result["candidate_id"]
        
        # 2. Trigger Formatting (CVWriterAgent)
        if use_sync_tasks():
            format_result = format_cv_task(candidate_id)
        else:
            format_result = format_cv_task.apply_async(args=[candidate_id], queue="agent_queue")

        # 3. Trigger Job Search (JobSearchAgent)
        search_keywords = keywords or []
        if isinstance(search_keywords, str):
            search_keywords = [keyword.strip() for keyword in search_keywords.split(",") if keyword.strip()]
        if not search_keywords:
            db = SessionLocal()
            try:
                from backend.app.models.candidate import Candidate
                candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
                if candidate and candidate.skills:
                    search_keywords = [skill.skill_name for skill in candidate.skills[:5]]
            finally:
                db.close()
        if not search_keywords:
            search_keywords = load_settings().default_keywords or FALLBACK_KEYWORDS

        if use_sync_tasks():
            search_result = keyword_search_workflow_task(
                search_keywords,
                candidate_id,
                None,
                source_url,
                search_mode,
            )
        else:
            search_result = keyword_search_workflow_task.apply_async(
                args=[search_keywords, candidate_id, None, source_url, search_mode],
                queue="agent_queue",
            )
        
        # 4. Final Match (MatchingAgent) is usually triggered inside the keyword_search_workflow_task
        # but we could also trigger a candidate-specific match search here if needed.
        
        if use_sync_tasks():
            return {
                "status": "success",
                "candidate_id": candidate_id,
                "format_result": format_result,
                "search_result": search_result,
            }

        return {"status": "workflow_started", "candidate_id": candidate_id}
    
    return result
