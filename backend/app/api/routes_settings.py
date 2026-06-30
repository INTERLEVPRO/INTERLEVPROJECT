from pathlib import Path
from typing import Any, Dict
import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from backend.app.services.app_settings import (
    get_agent_blueprint,
    load_settings,
    merge_settings_update,
    public_settings,
    save_settings,
)


router = APIRouter()
CV_TEMPLATE_DIR = (
    Path(tempfile.gettempdir()) / "interlev-agent" / "cv_templates"
    if os.getenv("VERCEL")
    else Path("cv_templates")
)
CV_TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
CV_TEMPLATE_MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
}


@router.get("/")
def get_settings():
    return public_settings()


@router.put("/")
def update_settings(payload: Dict[str, Any]):
    settings = merge_settings_update(payload)
    return public_settings(settings)


@router.post("/cv-template")
async def upload_cv_template(file: UploadFile = File(...)):
    filename = Path(file.filename or "cv_template").name
    extension = Path(filename).suffix.lower().lstrip(".")
    accepted = {"docx", "pdf", "txt", "md"}
    if extension not in accepted:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported CV template format. Accepted formats: {', '.join(sorted(accepted))}",
        )

    safe_name = "".join(ch if ch.isalnum() or ch in "._- " else "_" for ch in filename).strip()
    template_path = CV_TEMPLATE_DIR / safe_name
    with template_path.open("wb") as buffer:
        buffer.write(await file.read())

    settings = load_settings()
    settings.cv_format.template_file_path = str(template_path)
    settings.cv_format.template_file_name = safe_name
    if not settings.cv_format.template_name or settings.cv_format.template_name == "INTERLEV Professional":
        settings.cv_format.template_name = Path(safe_name).stem.replace("_", " ").strip() or settings.cv_format.template_name
    save_settings(settings)
    return public_settings(settings)


@router.get("/cv-template")
def get_cv_template():
    settings = load_settings()
    template_path = _current_template_path(settings)
    return {
        "template_name": settings.cv_format.template_name,
        "template_file_name": settings.cv_format.template_file_name,
        "template_file_path": settings.cv_format.template_file_path,
        "size_bytes": template_path.stat().st_size,
        "extension": template_path.suffix.lower().lstrip("."),
    }


@router.get("/cv-template/view")
def view_cv_template():
    settings = load_settings()
    template_path = _current_template_path(settings)
    media_type = CV_TEMPLATE_MEDIA_TYPES.get(template_path.suffix.lower(), "application/octet-stream")
    return FileResponse(
        str(template_path),
        media_type=media_type,
        filename=settings.cv_format.template_file_name or template_path.name,
        headers={
            "Content-Disposition": f'inline; filename="{settings.cv_format.template_file_name or template_path.name}"'
        },
    )


@router.get("/cv-template/content")
def get_cv_template_content():
    settings = load_settings()
    template_path = _current_template_path(settings)
    if template_path.suffix.lower() not in {".txt", ".md"}:
        raise HTTPException(status_code=400, detail="Only TXT and MD templates can be edited as text.")
    return {
        "template_name": settings.cv_format.template_name,
        "template_file_name": settings.cv_format.template_file_name,
        "content": template_path.read_text(encoding="utf-8", errors="ignore"),
    }


@router.put("/cv-template")
def update_cv_template(payload: Dict[str, Any]):
    settings = load_settings()
    template_path = _current_template_path(settings)
    template_name = str(payload.get("template_name") or "").strip()
    if template_name:
        settings.cv_format.template_name = template_name

    if "content" in payload:
        if template_path.suffix.lower() not in {".txt", ".md"}:
            raise HTTPException(status_code=400, detail="Only TXT and MD templates can be edited as text.")
        template_path.write_text(str(payload.get("content") or ""), encoding="utf-8")

    save_settings(settings)
    return public_settings(settings)


@router.delete("/cv-template")
def delete_cv_template():
    settings = load_settings()
    template_path = Path(settings.cv_format.template_file_path or "")
    if template_path.exists() and template_path.is_file():
        template_path.unlink()
    settings.cv_format.template_file_path = ""
    settings.cv_format.template_file_name = ""
    settings.cv_format.template_name = "INTERLEV Professional"
    save_settings(settings)
    return public_settings(settings)


@router.get("/agent-blueprint")
def agent_blueprint():
    return get_agent_blueprint()


@router.get("/health")
def settings_health():
    settings = load_settings()
    enabled_sources = [
        source.label
        for source in settings.job_sources
        if settings.automation.search_scope == "all_freelance_sources" or source.enabled
    ]
    return {
        "company_name": settings.branding.company_name,
        "company_url": settings.branding.company_url,
        "active_provider": settings.ai.active_provider,
        "autonomy_level": settings.automation.autonomy_level,
        "enabled_job_sources": enabled_sources,
        "mcp_enabled": [
            connector.label for connector in settings.mcp_connectors if connector.enabled
        ],
        "mcp_server": {
            "status": "available",
            "http_base": "/api/mcp",
            "stdio_module": "backend.mcp_server",
        },
    }


def _current_template_path(settings) -> Path:
    template_path = Path(settings.cv_format.template_file_path or "")
    if not settings.cv_format.template_file_name or not template_path.exists() or not template_path.is_file():
        raise HTTPException(status_code=404, detail="No CV format template has been uploaded.")
    return template_path
