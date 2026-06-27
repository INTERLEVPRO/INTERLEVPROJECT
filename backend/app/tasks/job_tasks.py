from backend.app.tasks.celery_app import celery_app
from backend.app.database import SessionLocal
from backend.app.agents.job_search_agent import JobSearchAgent
from backend.app.agents.job_parser_agent import JobParserAgent
from backend.app.agents.matching_agent import MatchingAgent
from backend.app.services.llm.factory import get_llm_provider
from backend.app.models.candidate import Candidate
from backend.app.models.match import Match
from backend.app.agents.logging_agent import LoggingAgent
from backend.app.agents.notification_agent import NotificationAgent
from backend.app.services.application_service import ApplicationDraftService
from backend.app.services.app_settings import load_settings
from typing import List, Optional

@celery_app.task(name="keyword_search_workflow_task")
def keyword_search_workflow_task(
    keywords: List[str],
    candidate_id: Optional[int] = None,
    source_keys: Optional[List[str]] = None,
    source_url: Optional[str] = None,
    search_mode: str = "real_search",
):
    db = SessionLocal()
    llm = get_llm_provider()
    
    search_agent = JobSearchAgent()
    parser_agent = JobParserAgent(llm)
    matcher = MatchingAgent()
    application_service = ApplicationDraftService()
    settings = load_settings()
    
    try:
        if candidate_id and not keywords:
            candidate_for_keywords = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if candidate_for_keywords and candidate_for_keywords.skills:
                keywords = [skill.skill_name for skill in candidate_for_keywords.skills[:5]]

        # 1. Search for jobs
        LoggingAgent.log_action(
            db,
            "Job Searcher",
            "Searching portals",
            "working",
            input_data={"keywords": keywords, "source_url": source_url, "search_mode": search_mode},
        )
        fast_pass = (search_mode or "").lower() == "fast_pass"
        NotificationAgent.notify(
            db,
            "Website search started",
            "Fast Pass is creating local job leads from the CV skills."
            if fast_pass
            else "Searching enabled freelance websites for matching work.",
            "info",
            "job_search",
            {
                "keywords": keywords,
                "candidate_id": candidate_id,
                "source_keys": source_keys,
                "source_url": source_url,
                "search_mode": search_mode,
            },
        )
        jobs = search_agent.search_jobs(
            db,
            keywords,
            candidate_id=candidate_id,
            source_keys=source_keys,
            source_url=source_url,
            search_mode=search_mode,
        )
        search_stats = search_agent.last_stats
        LoggingAgent.log_action(
            db,
            "Job Searcher",
            "Searching portals",
            "success",
            output_data={"jobs_found": len(jobs), **search_stats},
        )
        skipped = search_stats.get("skipped_sources", [])
        errors = search_stats.get("errors", [])
        NotificationAgent.notify(
            db,
            "Website search finished",
            f"Fast Pass created {len(jobs)} local job leads from the CV skills."
            if fast_pass
            else f"Found {len(jobs)} jobs. Skipped {len(skipped)} login-only sources.",
            "success" if jobs else "warning",
            "job_search",
            {"jobs_found": len(jobs), **search_stats},
        )
        for skipped_source in skipped:
            NotificationAgent.notify(
                db,
                "Source needs connector",
                f"{skipped_source['source']} needs login/connector access before it can be searched.",
                "warning",
                "job_search",
                skipped_source,
            )
        for error in errors:
            NotificationAgent.notify(
                db,
                "Source search failed",
                f"{error['source']} could not be searched: {error['error']}",
                "error",
                "job_search",
                error,
            )
        
        # 2. Parse jobs and match against all active candidates
        if candidate_id:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            candidates = [candidate] if candidate and candidate.profile_status == "complete" else []
        else:
            candidates = db.query(Candidate).filter(Candidate.profile_status == "complete").all()
        
        results = []
        application_count = 0
        threshold = max(50, int(settings.automation.min_match_score or 50))
        for job in jobs:
            # Parse job
            if not fast_pass:
                try:
                    parser_agent.parse_job_description(db, job)
                except Exception as exc:
                    LoggingAgent.log_action(db, "Job Parser", f"Parsing Job #{job.id}", "error", error_message=str(exc))
            
            # Match against each candidate
            for candidate in candidates:
                LoggingAgent.log_action(db, "Matcher", f"Matching Candidate #{candidate.id}", "working")
                match_data = matcher.calculate_match(candidate, job)
                LoggingAgent.log_action(db, "Matcher", f"Matching Candidate #{candidate.id}", "success", output_data=match_data)
                
                # Save match
                if match_data["match_percentage"] >= threshold:
                    existing = db.query(Match).filter(
                        Match.candidate_id == candidate.id,
                        Match.job_id == job.id,
                    ).first()
                    if existing:
                        existing.match_percentage = match_data["match_percentage"]
                        existing.match_level = match_data["match_level"]
                        existing.matched_skills = match_data["matched_skills"]
                        existing.missing_skills = match_data["missing_skills"]
                        existing.reason = match_data["reason"]
                    else:
                        match_record = Match(
                            candidate_id=candidate.id,
                            job_id=job.id,
                            match_percentage=match_data["match_percentage"],
                            match_level=match_data["match_level"],
                            matched_skills=match_data["matched_skills"],
                            missing_skills=match_data["missing_skills"],
                            reason=match_data["reason"]
                        )
                        db.add(match_record)
                    NotificationAgent.notify(
                        db,
                        "Match found",
                        f"{candidate.name} matches {job.title} at {match_data['match_percentage']}%.",
                        "success",
                        "match",
                        {"candidate_id": candidate.id, "job_id": job.id, "score": match_data["match_percentage"]},
                    )
                    if not fast_pass:
                        try:
                            application = application_service.draft_for_candidate_job(
                                db,
                                candidate,
                                job,
                                float(match_data["match_percentage"]),
                            )
                            application_count += 1
                            LoggingAgent.log_action(
                                db,
                                "Application Writer",
                                f"Application #{application.id}",
                                "success",
                                output_data={
                                    "application_id": application.id,
                                    "status": application.status,
                                },
                            )
                        except Exception as exc:
                            LoggingAgent.log_action(
                                db,
                                "Application Writer",
                                f"Draft for Candidate #{candidate.id}",
                                "error",
                                error_message=str(exc),
                            )
                            NotificationAgent.notify(
                                db,
                                "Application draft failed",
                                str(exc),
                                "error",
                                "application",
                                {"candidate_id": candidate.id, "job_id": job.id},
                            )
                    results.append({
                        "job_id": job.id,
                        "candidate_id": candidate.id,
                        "score": match_data["match_percentage"]
                    })
        
        db.commit()
        NotificationAgent.notify(
            db,
            "Matching finished",
            f"Fast Pass saved {len(results)} matches at or above {threshold}%."
            if fast_pass
            else f"Saved {len(results)} matches and {application_count} application drafts at or above {threshold}%.",
            "success" if results else "warning",
            "match",
            {
                "matches_found": len(results),
                "applications_created": application_count,
                "threshold": threshold,
                "candidate_id": candidate_id,
            },
        )
        return {
            "status": "success",
            "searched_sources": len(search_stats.get("searched_sources", [])),
            "jobs_found": len(jobs),
            "matches_found": len(results),
            "applications_created": application_count,
            "threshold": threshold,
        }
    except Exception as e:
        db.rollback()
        LoggingAgent.log_action(db, "Job Searcher", "Search Error", "error", error_message=str(e))
        NotificationAgent.notify(
            db,
            "Job search failed",
            str(e),
            "error",
            "job_search",
            {"keywords": keywords, "source_url": source_url},
        )
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task(name="search_matching_candidates_task")
def search_matching_candidates_task(job_id: int):
    """
    Given a job, find the best matching candidates from the database.
    """
    db = SessionLocal()
    matcher = MatchingAgent()
    settings = load_settings()
    
    try:
        from backend.app.models.job import Job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return {"status": "error", "message": "Job not found"}

        candidates = db.query(Candidate).filter(Candidate.profile_status == "complete").all()
        
        matches = []
        threshold = max(50, int(settings.automation.min_match_score or 50))
        for candidate in candidates:
            match_data = matcher.calculate_match(candidate, job)
            if match_data["match_percentage"] >= threshold:
                match_record = db.query(Match).filter(
                    Match.candidate_id == candidate.id,
                    Match.job_id == job.id,
                ).first()
                if match_record:
                    match_record.match_percentage = match_data["match_percentage"]
                    match_record.match_level = match_data["match_level"]
                    match_record.matched_skills = match_data["matched_skills"]
                    match_record.missing_skills = match_data["missing_skills"]
                    match_record.reason = match_data["reason"]
                else:
                    match_record = Match(
                        candidate_id=candidate.id,
                        job_id=job.id,
                        match_percentage=match_data["match_percentage"],
                        match_level=match_data["match_level"],
                        matched_skills=match_data["matched_skills"],
                        missing_skills=match_data["missing_skills"],
                        reason=match_data["reason"]
                    )
                    db.add(match_record)
                matches.append(candidate.id)
        
        db.commit()
        return {"status": "success", "candidates_matched": len(matches)}
    except Exception as e:
        db.rollback()
        LoggingAgent.log_action(db, "Matcher", "Matching Error", "error", error_message=str(e))
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
