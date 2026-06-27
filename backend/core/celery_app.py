"""Compatibility import for legacy code paths.

The active Celery configuration lives in backend.app.tasks.celery_app.
Keep this module so older imports still share the same app instance.
"""

from backend.app.tasks.celery_app import celery_app
