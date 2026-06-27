from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from celery.result import AsyncResult
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from backend.app.agents.job_search_agent import JobSearchAgent
from backend.app.agents.matching_agent import MatchingAgent
from backend.app.database import SessionLocal
from backend.app.models.agent_log import AgentLog
from backend.app.models.application import Application
from backend.app.models.candidate import Candidate
from backend.app.models.cv import CV
from backend.app.models.job import Job
from backend.app.models.match import Match
from backend.app.models.notification import Notification
from backend.app.models.review import ReviewItem
from backend.app.services.app_settings import (
    get_agent_blueprint,
    load_settings,
    merge_settings_update,
    public_settings,
    save_settings,
)
from backend.app.services.application_service import (
    ApplicationDraftService,
    application_to_dict,
)
from backend.app.tasks.celery_app import celery_app
from backend.app.tasks.cv_tasks import parse_cv_task, run_full_recruitment_workflow
from backend.app.tasks.formatting_tasks import format_cv_task
from backend.app.tasks.job_tasks import keyword_search_workflow_task


PROJECT_ROOT = Path(__file__).resolve().parents[3]

JSON_SCHEMA_OBJECT = {"type": "object", "properties": {}, "additionalProperties": False}


def list_mcp_tools() -> List[Dict[str, Any]]:
    return [
        {
            "name": "interlev_health",
            "description": "Return INTERLEV API, database, settings, connector, and record-count health.",
            "inputSchema": JSON_SCHEMA_OBJECT,
        },
        {
            "name": "interlev_get_settings",
            "description": "Return public application settings with API keys redacted.",
            "inputSchema": JSON_SCHEMA_OBJECT,
        },
        {
            "name": "interlev_update_settings",
            "description": "Merge a settings payload into app_settings.json. API keys are preserved when blank.",
            "inputSchema": {
                "type": "object",
                "properties": {"payload": {"type": "object"}},
                "required": ["payload"],
                "additionalProperties": False,
            },
        },
        {
            "name": "interlev_prepare_mcp_connectors",
            "description": "Enable all configured MCP connector toggles and mark them as available through the local bridge. External account authorization is still separate.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "default": "local_mcp_available",
                    }
                },
                "additionalProperties": False,
            },
        },
        {
            "name": "interlev_list_candidates",
            "description": "List candidate profiles.",
            "inputSchema": _list_schema(
                {
                    "status": {"type": "string"},
                    "search": {"type": "string"},
                }
            ),
        },
        {
            "name": "interlev_get_candidate",
            "description": "Get one candidate with skills, CVs, and matches.",
            "inputSchema": _id_schema("candidate_id"),
        },
        {
            "name": "interlev_list_cvs",
            "description": "List uploaded and parsed CV records.",
            "inputSchema": _list_schema({"candidate_id": {"type": "integer"}}),
        },
        {
            "name": "interlev_parse_cv_file",
            "description": "Queue parsing for an existing CV file inside this project workspace.",
            "inputSchema": {
                "type": "object",
                "properties": {"file_path": {"type": "string"}},
                "required": ["file_path"],
                "additionalProperties": False,
            },
        },
        {
            "name": "interlev_format_candidate_cv",
            "description": "Queue formatted CV generation for a candidate.",
            "inputSchema": _id_schema("candidate_id"),
        },
        {
            "name": "interlev_run_full_campaign_from_file",
            "description": "Queue the full recruitment campaign for an existing CV file inside this project workspace.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": [],
                    },
                    "source_url": {"type": "string", "default": ""},
                    "search_mode": {"type": "string", "default": "real_search"},
                },
                "required": ["file_path"],
                "additionalProperties": False,
            },
        },
        {
            "name": "interlev_list_jobs",
            "description": "List discovered job records.",
            "inputSchema": _list_schema(
                {
                    "status": {"type": "string"},
                    "platform": {"type": "string"},
                    "search": {"type": "string"},
                }
            ),
        },
        {
            "name": "interlev_get_job",
            "description": "Get one job record.",
            "inputSchema": _id_schema("job_id"),
        },
        {
            "name": "interlev_start_job_search",
            "description": "Queue a keyword job search workflow.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "candidate_id": {"type": ["integer", "null"]},
                    "source_keys": {
                        "type": ["array", "null"],
                        "items": {"type": "string"},
                    },
                    "source_url": {"type": ["string", "null"]},
                    "search_mode": {"type": "string", "default": "real_search"},
                },
                "required": ["keywords"],
                "additionalProperties": False,
            },
        },
        {
            "name": "interlev_list_matches",
            "description": "List saved candidate/job matches.",
            "inputSchema": _list_schema(
                {
                    "candidate_id": {"type": "integer"},
                    "job_id": {"type": "integer"},
                    "status": {"type": "string"},
                }
            ),
        },
        {
            "name": "interlev_run_match",
            "description": "Run matching for one candidate and one job and save/update the match.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "candidate_id": {"type": "integer"},
                    "job_id": {"type": "integer"},
                    "allow_below_threshold": {"type": "boolean", "default": True},
                },
                "required": ["candidate_id", "job_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "interlev_list_applications",
            "description": "List application drafts and send-status records.",
            "inputSchema": _list_schema(
                {
                    "candidate_id": {"type": "integer"},
                    "job_id": {"type": "integer"},
                    "status": {"type": "string"},
                }
            ),
        },
        {
            "name": "interlev_draft_application",
            "description": "Create or refresh an application draft for a candidate/job pair.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "candidate_id": {"type": "integer"},
                    "job_id": {"type": "integer"},
                    "match_score": {"type": ["number", "null"]},
                    "force_refresh": {"type": "boolean", "default": False},
                    "status": {"type": ["string", "null"]},
                },
                "required": ["candidate_id", "job_id"],
                "additionalProperties": False,
            },
        },
        {
            "name": "interlev_list_review_items",
            "description": "List human review queue items.",
            "inputSchema": _list_schema({"status": {"type": "string"}}),
        },
        {
            "name": "interlev_list_notifications",
            "description": "List user/admin notifications.",
            "inputSchema": _list_schema(
                {
                    "category": {"type": "string"},
                    "unread_only": {"type": "boolean"},
                }
            ),
        },
        {
            "name": "interlev_list_agent_logs",
            "description": "List agent audit logs.",
            "inputSchema": _list_schema(
                {
                    "agent_name": {"type": "string"},
                    "status": {"type": "string"},
                }
            ),
        },
        {
            "name": "interlev_get_task_status",
            "description": "Get Celery task state/result by task_id.",
            "inputSchema": {
                "type": "object",
                "properties": {"task_id": {"type": "string"}},
                "required": ["task_id"],
                "additionalProperties": False,
            },
        },
    ]


def list_mcp_resources() -> List[Dict[str, Any]]:
    resources = [
        ("interlev://settings", "INTERLEV Settings", "Current public settings with secrets redacted"),
        ("interlev://agent-blueprint", "INTERLEV Agent Blueprint", "Agent responsibilities, tools, and outputs"),
        ("interlev://health", "INTERLEV Health", "Counts and connector status"),
        ("interlev://candidates", "INTERLEV Candidates", "Candidate profile records"),
        ("interlev://cvs", "INTERLEV CVs", "Uploaded and formatted CV records"),
        ("interlev://jobs", "INTERLEV Jobs", "Discovered job records"),
        ("interlev://matches", "INTERLEV Matches", "Candidate/job match records"),
        ("interlev://applications", "INTERLEV Applications", "Application draft and status records"),
        ("interlev://review", "INTERLEV Review Queue", "Human review queue items"),
        ("interlev://notifications", "INTERLEV Notifications", "System/user notifications"),
        ("interlev://agent-logs", "INTERLEV Agent Logs", "Agent audit logs"),
    ]
    return [
        {
            "uri": uri,
            "name": name,
            "description": description,
            "mimeType": "application/json",
        }
        for uri, name, description in resources
    ]


def read_mcp_resource(uri: str) -> Dict[str, Any]:
    resource_tools = {
        "interlev://settings": ("interlev_get_settings", {}),
        "interlev://agent-blueprint": ("agent_blueprint", {}),
        "interlev://health": ("interlev_health", {}),
        "interlev://candidates": ("interlev_list_candidates", {"limit": 100}),
        "interlev://cvs": ("interlev_list_cvs", {"limit": 100}),
        "interlev://jobs": ("interlev_list_jobs", {"limit": 100}),
        "interlev://matches": ("interlev_list_matches", {"limit": 100}),
        "interlev://applications": ("interlev_list_applications", {"limit": 100}),
        "interlev://review": ("interlev_list_review_items", {"limit": 100}),
        "interlev://notifications": ("interlev_list_notifications", {"limit": 100}),
        "interlev://agent-logs": ("interlev_list_agent_logs", {"limit": 100}),
    }
    if uri not in resource_tools:
        raise ValueError(f"Unknown MCP resource URI: {uri}")
    tool_name, args = resource_tools[uri]
    if tool_name == "agent_blueprint":
        return get_agent_blueprint()
    return call_mcp_tool(tool_name, args)


def call_mcp_tool(
    name: str,
    arguments: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
) -> Any:
    arguments = arguments or {}
    handlers: Dict[str, Callable[[Session, Dict[str, Any]], Any]] = {
        "interlev_health": _health,
        "interlev_get_settings": _get_settings,
        "interlev_update_settings": _update_settings,
        "interlev_prepare_mcp_connectors": _prepare_mcp_connectors,
        "interlev_list_candidates": _list_candidates,
        "interlev_get_candidate": _get_candidate,
        "interlev_list_cvs": _list_cvs,
        "interlev_parse_cv_file": _parse_cv_file,
        "interlev_format_candidate_cv": _format_candidate_cv,
        "interlev_run_full_campaign_from_file": _run_full_campaign_from_file,
        "interlev_list_jobs": _list_jobs,
        "interlev_get_job": _get_job,
        "interlev_start_job_search": _start_job_search,
        "interlev_list_matches": _list_matches,
        "interlev_run_match": _run_match,
        "interlev_list_applications": _list_applications,
        "interlev_draft_application": _draft_application,
        "interlev_list_review_items": _list_review_items,
        "interlev_list_notifications": _list_notifications,
        "interlev_list_agent_logs": _list_agent_logs,
        "interlev_get_task_status": _get_task_status,
    }
    if name not in handlers:
        raise ValueError(f"Unknown MCP tool: {name}")

    owns_session = db is None
    session = db or SessionLocal()
    try:
        return jsonable_encoder(handlers[name](session, arguments))
    finally:
        if owns_session:
            session.close()


def _list_schema(extra_properties: Dict[str, Any]) -> Dict[str, Any]:
    properties = {
        "limit": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50},
        **extra_properties,
    }
    return {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }


def _id_schema(field_name: str) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {field_name: {"type": "integer"}},
        "required": [field_name],
        "additionalProperties": False,
    }


def _limit(arguments: Dict[str, Any], default: int = 50) -> int:
    raw_limit = arguments.get("limit", default)
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        limit = default
    return max(1, min(limit, 500))


def _require_int(arguments: Dict[str, Any], key: str) -> int:
    value = arguments.get(key)
    if value is None:
        raise ValueError(f"Missing required argument: {key}")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer") from exc


def _workspace_file(file_path: str) -> str:
    path = Path(file_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    resolved = path.resolve()
    if PROJECT_ROOT not in resolved.parents and resolved != PROJECT_ROOT:
        raise ValueError("file_path must point inside the INTERLEV project workspace")
    if not resolved.exists() or not resolved.is_file():
        raise ValueError(f"file_path does not exist: {file_path}")
    return str(resolved.relative_to(PROJECT_ROOT))


def _health(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    settings = load_settings()
    connectors = [
        {
            "key": connector.key,
            "label": connector.label,
            "enabled": connector.enabled,
            "status": connector.status,
        }
        for connector in settings.mcp_connectors
    ]
    return {
        "service": "interlev-local-mcp",
        "status": "ok",
        "api": "available",
        "mcp_http_base": "/api/mcp",
        "mcp_stdio_module": "backend.mcp_server",
        "active_provider": settings.ai.active_provider,
        "autonomy_level": settings.automation.autonomy_level,
        "connectors": connectors,
        "counts": {
            "candidates": db.query(Candidate).count(),
            "cvs": db.query(CV).count(),
            "jobs": db.query(Job).count(),
            "matches": db.query(Match).count(),
            "applications": db.query(Application).count(),
            "review_items": db.query(ReviewItem).count(),
            "notifications": db.query(Notification).count(),
            "agent_logs": db.query(AgentLog).count(),
        },
    }


def _get_settings(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    return public_settings()


def _update_settings(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    payload = arguments.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    return public_settings(merge_settings_update(payload))


def _prepare_mcp_connectors(db: Session, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    status = str(arguments.get("status") or "local_mcp_available")
    settings = load_settings()
    for connector in settings.mcp_connectors:
        connector.enabled = True
        connector.status = status
    save_settings(settings)
    return public_settings(settings)["mcp_connectors"]


def _list_candidates(db: Session, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = db.query(Candidate)
    status = arguments.get("status")
    if status:
        query = query.filter(Candidate.profile_status == status)
    search = arguments.get("search")
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Candidate.name.ilike(like))
            | (Candidate.email.ilike(like))
            | (Candidate.main_role.ilike(like))
            | (Candidate.summary.ilike(like))
        )
    candidates = query.order_by(Candidate.created_at.desc()).limit(_limit(arguments)).all()
    return [_candidate_summary(candidate) for candidate in candidates]


def _get_candidate(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    candidate_id = _require_int(arguments, "candidate_id")
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise ValueError("Candidate not found")
    matches = db.query(Match).filter(Match.candidate_id == candidate_id).all()
    return {
        **_candidate_summary(candidate),
        "skills": [
            {
                "skill_name": skill.skill_name,
                "skill_level": skill.skill_level,
                "years_experience": skill.years_experience,
            }
            for skill in candidate.skills
        ],
        "cvs": [_cv_summary(cv) for cv in candidate.cvs],
        "matches": [_match_summary(match, db) for match in matches],
    }


def _list_cvs(db: Session, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = db.query(CV)
    if arguments.get("candidate_id") is not None:
        query = query.filter(CV.candidate_id == _require_int(arguments, "candidate_id"))
    cvs = query.order_by(CV.created_at.desc()).limit(_limit(arguments)).all()
    return [_cv_summary(cv) for cv in cvs]


def _parse_cv_file(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    file_path = _workspace_file(str(arguments.get("file_path") or ""))
    task = parse_cv_task.delay(file_path)
    return {"message": "CV parsing queued", "task_id": task.id, "file_path": file_path}


def _format_candidate_cv(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    candidate_id = _require_int(arguments, "candidate_id")
    if not db.query(Candidate).filter(Candidate.id == candidate_id).first():
        raise ValueError("Candidate not found")
    task = format_cv_task.delay(candidate_id)
    return {"message": "CV formatting queued", "task_id": task.id, "candidate_id": candidate_id}


def _run_full_campaign_from_file(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    file_path = _workspace_file(str(arguments.get("file_path") or ""))
    keywords = arguments.get("keywords") or []
    if not isinstance(keywords, list):
        raise ValueError("keywords must be a list of strings")
    clean_keywords = [str(keyword).strip() for keyword in keywords if str(keyword).strip()]
    source_url = str(arguments.get("source_url") or "").strip()
    search_mode = "real_search"
    JobSearchAgent().validate_source_url(source_url)
    task = run_full_recruitment_workflow.delay(file_path, clean_keywords, source_url, search_mode)
    return {
        "message": "Full recruitment campaign queued",
        "task_id": task.id,
        "file_path": file_path,
        "keywords": clean_keywords,
        "source_url": source_url,
        "search_mode": search_mode,
    }


def _list_jobs(db: Session, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = db.query(Job)
    if arguments.get("status"):
        query = query.filter(Job.status == arguments["status"])
    if arguments.get("platform"):
        query = query.filter(Job.platform == arguments["platform"])
    search = arguments.get("search")
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Job.title.ilike(like))
            | (Job.company.ilike(like))
            | (Job.description.ilike(like))
            | (Job.platform.ilike(like))
        )
    jobs = query.order_by(Job.created_at.desc()).limit(_limit(arguments)).all()
    return [_job_summary(job) for job in jobs]


def _get_job(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    job_id = _require_int(arguments, "job_id")
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError("Job not found")
    return _job_summary(job, include_description=True)


def _start_job_search(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    keywords = arguments.get("keywords") or []
    if not isinstance(keywords, list):
        raise ValueError("keywords must be a list of strings")
    clean_keywords = [str(keyword).strip() for keyword in keywords if str(keyword).strip()]
    if not clean_keywords:
        raise ValueError("At least one keyword is required")
    candidate_id = arguments.get("candidate_id")
    source_keys = arguments.get("source_keys")
    source_url = arguments.get("source_url")
    search_mode = "real_search"
    JobSearchAgent().validate_source_url(source_url)
    task = keyword_search_workflow_task.delay(
        clean_keywords,
        int(candidate_id) if candidate_id is not None else None,
        source_keys,
        source_url,
        search_mode,
    )
    return {"message": "Job search queued", "task_id": task.id, "keywords": clean_keywords}


def _list_matches(db: Session, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = db.query(Match)
    if arguments.get("candidate_id") is not None:
        query = query.filter(Match.candidate_id == _require_int(arguments, "candidate_id"))
    if arguments.get("job_id") is not None:
        query = query.filter(Match.job_id == _require_int(arguments, "job_id"))
    if arguments.get("status"):
        query = query.filter(Match.status == arguments["status"])
    matches = query.order_by(Match.created_at.desc()).limit(_limit(arguments)).all()
    return [_match_summary(match, db) for match in matches]


def _run_match(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    candidate_id = _require_int(arguments, "candidate_id")
    job_id = _require_int(arguments, "job_id")
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not candidate or not job:
        raise ValueError("Candidate or job not found")

    match_data = MatchingAgent().calculate_match(candidate, job)
    settings = load_settings()
    threshold = max(50, int(settings.automation.min_match_score or 50))
    allow_below_threshold = bool(arguments.get("allow_below_threshold", True))
    if match_data["match_percentage"] < threshold and not allow_below_threshold:
        raise ValueError(f"Match score is below {threshold}%")

    match_record = (
        db.query(Match)
        .filter(Match.candidate_id == candidate.id, Match.job_id == job.id)
        .first()
    )
    if not match_record:
        match_record = Match(candidate_id=candidate.id, job_id=job.id)
        db.add(match_record)

    match_record.match_percentage = match_data["match_percentage"]
    match_record.match_level = match_data["match_level"]
    match_record.matched_skills = match_data["matched_skills"]
    match_record.missing_skills = match_data["missing_skills"]
    match_record.reason = match_data["reason"]
    db.commit()
    db.refresh(match_record)
    return _match_summary(match_record, db)


def _list_applications(db: Session, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = db.query(Application)
    if arguments.get("candidate_id") is not None:
        query = query.filter(Application.candidate_id == _require_int(arguments, "candidate_id"))
    if arguments.get("job_id") is not None:
        query = query.filter(Application.job_id == _require_int(arguments, "job_id"))
    if arguments.get("status"):
        query = query.filter(Application.status == arguments["status"])
    applications = query.order_by(Application.created_at.desc()).limit(_limit(arguments)).all()
    return [application_to_dict(application, db) for application in applications]


def _draft_application(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    candidate_id = _require_int(arguments, "candidate_id")
    job_id = _require_int(arguments, "job_id")
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not candidate or not job:
        raise ValueError("Candidate or job not found")

    match_score = arguments.get("match_score")
    if match_score is None:
        match = (
            db.query(Match)
            .filter(Match.candidate_id == candidate_id, Match.job_id == job_id)
            .order_by(Match.created_at.desc())
            .first()
        )
        match_score = float(match.match_percentage) if match else 0.0

    application = ApplicationDraftService().draft_for_candidate_job(
        db,
        candidate,
        job,
        float(match_score),
        force_refresh=bool(arguments.get("force_refresh", False)),
        status=arguments.get("status"),
    )
    return application_to_dict(application, db)


def _list_review_items(db: Session, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = db.query(ReviewItem)
    if arguments.get("status"):
        query = query.filter(ReviewItem.status == arguments["status"])
    items = query.order_by(ReviewItem.created_at.desc()).limit(_limit(arguments)).all()
    return jsonable_encoder(items)


def _list_notifications(db: Session, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = db.query(Notification)
    if arguments.get("category"):
        query = query.filter(Notification.category == arguments["category"])
    if arguments.get("unread_only"):
        query = query.filter(Notification.is_read.is_(False))
    notifications = query.order_by(Notification.created_at.desc()).limit(_limit(arguments)).all()
    return jsonable_encoder(notifications)


def _list_agent_logs(db: Session, arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = db.query(AgentLog)
    if arguments.get("agent_name"):
        query = query.filter(AgentLog.agent_name == arguments["agent_name"])
    if arguments.get("status"):
        query = query.filter(AgentLog.status == arguments["status"])
    logs = query.order_by(AgentLog.created_at.desc()).limit(_limit(arguments)).all()
    return jsonable_encoder(logs)


def _get_task_status(db: Session, arguments: Dict[str, Any]) -> Dict[str, Any]:
    task_id = str(arguments.get("task_id") or "").strip()
    if not task_id:
        raise ValueError("task_id is required")
    task = AsyncResult(task_id, app=celery_app)
    response: Dict[str, Any] = {
        "task_id": task_id,
        "status": task.state,
        "ready": task.ready(),
        "successful": task.successful() if task.ready() else False,
    }
    if task.ready():
        response["result"] = jsonable_encoder(task.result)
    elif task.info:
        response["info"] = jsonable_encoder(task.info)
    return response


def _candidate_summary(candidate: Candidate) -> Dict[str, Any]:
    return {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "phone": candidate.phone,
        "location": candidate.location,
        "summary": candidate.summary,
        "main_role": candidate.main_role,
        "experience_years": candidate.experience_years,
        "experience_level": candidate.experience_level,
        "availability": candidate.availability,
        "expected_rate": candidate.expected_rate,
        "profile_status": candidate.profile_status,
        "created_at": candidate.created_at,
        "updated_at": candidate.updated_at,
    }


def _cv_summary(cv: CV) -> Dict[str, Any]:
    return {
        "id": cv.id,
        "candidate_id": cv.candidate_id,
        "original_file_path": cv.original_file_path,
        "formatted_cv_path": cv.formatted_cv_path,
        "parse_confidence": cv.parse_confidence,
        "status": cv.status,
        "created_at": cv.created_at,
        "parsed_text_preview": (cv.parsed_text or "")[:500],
    }


def _job_summary(job: Job, include_description: bool = False) -> Dict[str, Any]:
    data = {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "platform": job.platform,
        "url": job.url,
        "required_skills": job.required_skills,
        "nice_to_have_skills": job.nice_to_have_skills,
        "budget": job.budget,
        "location": job.location,
        "contract_type": job.contract_type,
        "posted_date": job.posted_date,
        "status": job.status,
        "created_at": job.created_at,
    }
    if include_description:
        data["description"] = job.description
    else:
        data["description_preview"] = (job.description or "")[:500]
    return data


def _match_summary(match: Match, db: Session) -> Dict[str, Any]:
    candidate = db.query(Candidate).filter(Candidate.id == match.candidate_id).first()
    job = db.query(Job).filter(Job.id == match.job_id).first()
    return {
        "id": match.id,
        "candidate_id": match.candidate_id,
        "candidate_name": candidate.name if candidate else None,
        "job_id": match.job_id,
        "job_title": job.title if job else None,
        "job_company": job.company if job else None,
        "match_percentage": match.match_percentage,
        "match_level": match.match_level,
        "matched_skills": match.matched_skills,
        "missing_skills": match.missing_skills,
        "reason": match.reason,
        "status": match.status,
        "created_at": match.created_at,
    }
