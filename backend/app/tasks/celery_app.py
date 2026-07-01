import os
import tempfile
from pathlib import Path

from celery import Celery


def use_sync_tasks() -> bool:
    """Run tasks inline for serverless/demo deployments that cannot run workers."""
    explicit = os.getenv("INTERLEV_SYNC_TASKS", "").strip().lower()
    if explicit in {"1", "true", "yes", "on"}:
        return True
    if explicit in {"0", "false", "no", "off"}:
        return False
    return bool(os.getenv("VERCEL"))


# Redis URL: use REDIS_URL if set, otherwise fallback to filesystem for local testing
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    broker_url = "filesystem://"
    runtime_dir = Path(tempfile.gettempdir()) / "interlev-agent" if os.getenv("VERCEL") else Path(".")
    broker_dir = runtime_dir / "celery_broker"
    results_dir = runtime_dir / "celery_results"
    processed_dir = broker_dir / "processed"
    result_backend = f"file://{results_dir}"

    broker_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    celery_app = Celery(
        "interlev_agent",
        broker=broker_url,
        backend=result_backend,
        include=[
            "backend.app.tasks.cv_tasks",
            "backend.app.tasks.job_tasks",
            "backend.app.tasks.formatting_tasks",
            "backend.tasks",
        ]
    )
    celery_app.conf.update(
        broker_transport_options={
            'data_folder_in': str(broker_dir),
            'data_folder_out': str(broker_dir),
            'data_folder_processed': str(processed_dir),
        }
    )
else:
    celery_app = Celery(
        "interlev_agent",
        broker=redis_url,
        backend=redis_url,
        include=[
            "backend.app.tasks.cv_tasks",
            "backend.app.tasks.job_tasks",
            "backend.app.tasks.formatting_tasks",
            "backend.tasks",
        ]
    )

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="agent_queue",
)
