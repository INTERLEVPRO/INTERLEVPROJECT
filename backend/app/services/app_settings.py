import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SETTINGS_PATH = (
    Path(tempfile.gettempdir()) / "interlev-agent" / "app_settings.json"
    if os.getenv("VERCEL")
    else PROJECT_ROOT / "app_settings.json"
)
SETTINGS_PATH = Path(os.getenv("INTERLEV_SETTINGS_PATH") or DEFAULT_SETTINGS_PATH)
if not SETTINGS_PATH.is_absolute():
    SETTINGS_PATH = PROJECT_ROOT / SETTINGS_PATH


class AIProviderSettings(BaseModel):
    active_provider: str = "mock"
    openai_api_key: str = ""
    gemini_api_key: str = ""
    openai_model: str = "gpt-4o"
    gemini_model: str = "gemini-2.0-flash"


class JobSourceSettings(BaseModel):
    key: str
    label: str
    url: str
    enabled: bool = True
    search_mode: str = "browser_or_api"
    auth_required: bool = False
    notes: str = ""


class CVFormatSettings(BaseModel):
    accepted_uploads: List[str] = Field(default_factory=lambda: ["pdf", "docx", "txt", "md"])
    output_format: str = "docx"
    template_name: str = "INTERLEV Professional"
    template_file_path: str = ""
    template_file_name: str = ""
    preserve_original: bool = True
    export_to_google_drive: bool = False


class MCPConnectorSettings(BaseModel):
    key: str
    label: str
    enabled: bool = False
    status: str = "not_connected"
    purpose: str = ""


class AutomationSettings(BaseModel):
    autonomy_level: str = "review_before_apply"
    search_scope: str = "selected_sources"
    min_match_score: int = 50
    max_jobs_per_source: int = 5
    inbox_scan_enabled: bool = False
    human_review_required: bool = True


class BrandingSettings(BaseModel):
    company_name: str = "INTERLEV"
    company_url: str = "https://interlev.ai"
    site_url: str = "https://interlev.ai"
    contact_email: str = "hello@interlev.ai"


class AppSettings(BaseModel):
    branding: BrandingSettings = Field(default_factory=BrandingSettings)
    ai: AIProviderSettings = Field(default_factory=AIProviderSettings)
    automation: AutomationSettings = Field(default_factory=AutomationSettings)
    cv_format: CVFormatSettings = Field(default_factory=CVFormatSettings)
    default_keywords: List[str] = Field(default_factory=lambda: ["Python", "FastAPI", "Backend"])
    job_sources: List[JobSourceSettings] = Field(default_factory=lambda: [
        JobSourceSettings(
            key="upwork",
            label="Upwork",
            url="https://www.upwork.com/nx/jobs/search/",
            auth_required=True,
            notes="Best used with logged-in browser automation or official integrations.",
        ),
        JobSourceSettings(
            key="freelancer",
            label="Freelancer",
            url="https://www.freelancer.com/jobs/",
        ),
        JobSourceSettings(
            key="freelancermap",
            label="Freelancermap",
            url="https://www.freelancermap.com/project-provider",
        ),
        JobSourceSettings(
            key="peopleperhour",
            label="PeoplePerHour",
            url="https://www.peopleperhour.com/freelance-jobs",
            auth_required=True,
        ),
        JobSourceSettings(
            key="guru",
            label="Guru",
            url="https://www.guru.com/d/jobs/",
        ),
        JobSourceSettings(
            key="toptal",
            label="Toptal",
            url="https://www.toptal.com/freelance-jobs",
            auth_required=True,
        ),
        JobSourceSettings(
            key="remoteok",
            label="Remote OK",
            url="https://remoteok.com/remote-dev-jobs",
        ),
        JobSourceSettings(
            key="weworkremotely",
            label="We Work Remotely",
            url="https://weworkremotely.com/remote-jobs/search",
        ),
        JobSourceSettings(
            key="linkedin",
            label="LinkedIn Jobs",
            url="https://www.linkedin.com/jobs/",
            auth_required=True,
            notes="Use only with approved account access and review before applying.",
        ),
    ])
    mcp_connectors: List[MCPConnectorSettings] = Field(default_factory=lambda: [
        MCPConnectorSettings(
            key="google_drive",
            label="Google Drive",
            purpose="Store uploaded CVs, formatted CVs, and campaign reports.",
        ),
        MCPConnectorSettings(
            key="gmail",
            label="Gmail Inbox",
            purpose="Read selected job invitation emails and draft replies.",
        ),
        MCPConnectorSettings(
            key="google_calendar",
            label="Google Calendar",
            purpose="Schedule interviews and reminders after human approval.",
        ),
        MCPConnectorSettings(
            key="slack",
            label="Slack",
            purpose="Send campaign alerts to internal channels.",
        ),
        MCPConnectorSettings(
            key="notion",
            label="Notion",
            purpose="Publish candidate and job research notes.",
        ),
    ])


AGENT_BLUEPRINT: List[Dict[str, Any]] = [
    {
        "agent": "Orchestrator Agent",
        "purpose": "Plans the campaign, assigns work, checks settings, and decides when human approval is needed.",
        "skills": ["workflow planning", "queue control", "policy checks", "error recovery"],
        "tools": ["Celery", "FastAPI", "settings service", "audit logs"],
        "output": "Campaign plan, task queue, final status",
        "human_input": "Autonomy level, target role, approval rules",
    },
    {
        "agent": "CV Intake Agent",
        "purpose": "Accepts PDF, DOCX, or TXT CVs and stores the original safely.",
        "skills": ["file validation", "format detection", "duplicate checks"],
        "tools": ["FastAPI UploadFile", "local storage", "Google Drive MCP optional"],
        "output": "Stored CV file path and intake log",
        "human_input": "Upload CV and select target output format",
    },
    {
        "agent": "CV Reader Agent",
        "purpose": "Extracts text and structured candidate information from the CV.",
        "skills": ["PDF parsing", "DOCX parsing", "LLM JSON extraction"],
        "tools": ["pdfplumber", "python-docx", "OpenAI/Gemini/Mock provider"],
        "output": "Name, email, skills, experience, location, raw text",
        "human_input": "Only if confidence is low",
    },
    {
        "agent": "Candidate Profile Agent",
        "purpose": "Creates a clean candidate profile and skill map for matching.",
        "skills": ["profile normalization", "skill cleanup", "experience grading"],
        "tools": ["SQLAlchemy", "LLM summary", "candidate database"],
        "output": "Complete candidate profile",
        "human_input": "Optional corrections",
    },
    {
        "agent": "CV Formatter Agent",
        "purpose": "Converts the candidate profile into an INTERLEV-branded professional CV.",
        "skills": ["DOCX generation", "template formatting", "role tailoring"],
        "tools": ["python-docx", "docx2pdf optional", "Google Drive MCP optional"],
        "output": "Formatted CV document",
        "human_input": "Template and output format choice",
    },
    {
        "agent": "Job Source Agent",
        "purpose": "Searches only the job websites enabled in Settings.",
        "skills": ["source selection", "keyword search", "deduplication"],
        "tools": ["source registry", "browser/API connectors", "Playwright planned"],
        "output": "Raw job leads",
        "human_input": "Allowed websites and keywords",
    },
    {
        "agent": "Inbox Agent",
        "purpose": "Reads approved inbox sources for job invitations and client messages.",
        "skills": ["email filtering", "thread summarization", "safe drafting"],
        "tools": ["Gmail MCP", "Outlook MCP optional", "audit logs"],
        "output": "Inbox job leads and reply drafts",
        "human_input": "Connector approval and mailbox scope",
    },
    {
        "agent": "Job Parser Agent",
        "purpose": "Turns job descriptions into structured requirements.",
        "skills": ["requirement extraction", "budget parsing", "contract classification"],
        "tools": ["LLM provider", "job database"],
        "output": "Structured job records",
        "human_input": "Only for unclear jobs",
    },
    {
        "agent": "Matching Agent",
        "purpose": "Scores each candidate against each job and explains the reason.",
        "skills": ["skill matching", "experience scoring", "location/rate checks"],
        "tools": ["matching rules", "candidate database", "job database"],
        "output": "Match percentage, missing skills, match reason",
        "human_input": "Minimum score threshold",
    },
    {
        "agent": "Application Writer Agent",
        "purpose": "Drafts job-specific proposals for approved matches.",
        "skills": ["proposal writing", "tone control", "client context use"],
        "tools": ["LLM provider", "formatted CV", "job record"],
        "output": "Application draft",
        "human_input": "Required before sending unless autonomy is changed",
    },
    {
        "agent": "Review Agent",
        "purpose": "Holds risky actions for human approval and records decisions.",
        "skills": ["quality gates", "approval routing", "risk labeling"],
        "tools": ["review queue", "audit logs"],
        "output": "Approved, rejected, or needs-edit decision",
        "human_input": "Final approval for apply/send actions",
    },
    {
        "agent": "QA and SEO/AEO Agent",
        "purpose": "Checks UI, metadata, structured data, logs, and end-to-end flows.",
        "skills": ["Playwright testing", "metadata checks", "accessibility smoke tests"],
        "tools": ["Codex", "Playwright", "MCP connectors", "FastAPI health checks"],
        "output": "Test report and improvement list",
        "human_input": "Production URL and target pages",
    },
]


def _model_dump(model: BaseModel) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def load_settings() -> AppSettings:
    if not SETTINGS_PATH.exists():
        settings = AppSettings()
        save_settings(settings)
        return settings

    with SETTINGS_PATH.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)
    return AppSettings(**data)


def save_settings(settings: AppSettings) -> AppSettings:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as file:
        json.dump(_model_dump(settings), file, indent=2)
    return settings


def public_settings(settings: AppSettings | None = None) -> Dict[str, Any]:
    settings = settings or load_settings()
    data = _model_dump(settings)
    ai = data.get("ai", {})
    ai["openai_api_key_configured"] = bool(ai.get("openai_api_key"))
    ai["gemini_api_key_configured"] = bool(ai.get("gemini_api_key"))
    ai["openai_api_key"] = ""
    ai["gemini_api_key"] = ""
    data["ai"] = ai
    return data


def merge_settings_update(payload: Dict[str, Any]) -> AppSettings:
    current = _model_dump(load_settings())

    def deep_update(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in update.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                base[key] = deep_update(base[key], value)
            else:
                base[key] = value
        return base

    ai_update = payload.get("ai", {})
    for secret_key in ("openai_api_key", "gemini_api_key"):
        if secret_key in ai_update and not ai_update.get(secret_key):
            ai_update.pop(secret_key)

    merged = deep_update(current, payload)
    settings = AppSettings(**merged)
    return save_settings(settings)


def enabled_job_sources(settings: AppSettings | None = None) -> List[JobSourceSettings]:
    settings = settings or load_settings()
    if settings.automation.search_scope == "all_freelance_sources":
        return settings.job_sources
    return [source for source in settings.job_sources if source.enabled]


def get_agent_blueprint() -> List[Dict[str, Any]]:
    return AGENT_BLUEPRINT
