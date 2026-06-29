from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "autoapply",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.task_routes = {
    "app.worker.parse_resume": {"queue": "parsing"},
    "app.worker.discover_jobs": {"queue": "discovery"},
    "app.worker.match_jobs": {"queue": "ai"},
    "app.worker.sync_email": {"queue": "email"},
    "app.worker.send_notification": {"queue": "notifications"},
}


@celery_app.task(name="app.worker.parse_resume", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def parse_resume(resume_id: str) -> dict[str, str]:
    return {"resume_id": resume_id, "status": "queued_for_parser"}


@celery_app.task(name="app.worker.discover_jobs", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def discover_jobs(user_id: str, source: str) -> dict[str, str]:
    return {"user_id": user_id, "source": source, "status": "queued_for_discovery"}


@celery_app.task(name="app.worker.match_jobs", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def match_jobs(user_id: str) -> dict[str, str]:
    return {"user_id": user_id, "status": "queued_for_matching"}


@celery_app.task(name="app.worker.sync_email", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def sync_email(user_id: str) -> dict[str, str]:
    return {"user_id": user_id, "status": "queued_for_email_sync"}


@celery_app.task(name="app.worker.send_notification", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_notification(notification_id: str) -> dict[str, str]:
    return {"notification_id": notification_id, "status": "queued_for_delivery"}

