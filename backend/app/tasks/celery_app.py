import os
from celery import Celery

# Redis URL: use REDIS_URL if set, otherwise fallback to filesystem for local testing
redis_url = os.getenv("REDIS_URL")
if not redis_url:
    broker_url = "filesystem://"
    result_backend = "file://./celery_results"
    
    os.makedirs("./celery_broker", exist_ok=True)
    os.makedirs("./celery_results", exist_ok=True)
    
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
            'data_folder_in': './celery_broker',
            'data_folder_out': './celery_broker',
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
