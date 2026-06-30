from fastapi import APIRouter

from app.api.deps import CurrentUser, UowDep

router = APIRouter()

# Human-readable labels for task names
TASK_LABELS: dict[str, str] = {
    "discover_jobs": "Job Discovery",
    "parse_resume": "Resume Parsing",
    "embed_profile": "Profile Embedding",
    "embed_job": "Job Embedding",
    "run_automation": "Auto-Apply",
    "submit_application": "Submit Application",
    "process_saved_search": "Saved Search Run",
    "send_notification": "Notification",
    "match_jobs": "Job Matching",
}

# Celery → our status mapping
CELERY_STATUS_MAP: dict[str, str] = {
    "PENDING": "pending",
    "RECEIVED": "pending",
    "STARTED": "running",
    "RETRY": "retrying",
    "SUCCESS": "success",
    "FAILURE": "failed",
    "REVOKED": "cancelled",
}


def _celery_status(celery_task_id: str) -> tuple[str, dict | None, str | None]:
    """Return (status, result, error) by querying the Celery result backend."""
    try:
        from app.worker import celery_app
        res = celery_app.AsyncResult(celery_task_id)
        celery_state = res.state
        status = CELERY_STATUS_MAP.get(celery_state, "pending")
        result: dict | None = None
        error: str | None = None
        if celery_state == "SUCCESS" and isinstance(res.result, dict):
            result = res.result
        elif celery_state == "FAILURE":
            error = str(res.result)
        return status, result, error
    except Exception:
        return "unknown", None, None


@router.get("")
async def list_tasks(current_user: CurrentUser, uow: UowDep) -> list[dict]:
    logs = await uow.task_logs.list_for_user(current_user.id, limit=100)

    tasks = []
    for log in logs:
        # Refresh live status from Celery for non-terminal tasks
        if log.status in ("pending", "running", "retrying"):
            live_status, live_result, live_error = _celery_status(log.celery_task_id)
            if live_status != log.status:
                await uow.task_logs.update_status(log.celery_task_id, live_status, live_result, live_error)
                await uow.commit()
                log.status = live_status
                if live_result:
                    log.result = live_result
                if live_error:
                    log.error = live_error

        tasks.append(_serialize(log))

    return tasks


@router.get("/{celery_task_id}")
async def get_task(celery_task_id: str, current_user: CurrentUser, uow: UowDep) -> dict:
    from fastapi import HTTPException
    log = await uow.task_logs.get_by_celery_id(celery_task_id)
    if log is None or log.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")

    if log.status in ("pending", "running", "retrying"):
        live_status, live_result, live_error = _celery_status(celery_task_id)
        if live_status != log.status:
            await uow.task_logs.update_status(celery_task_id, live_status, live_result, live_error)
            await uow.commit()
            log.status = live_status
            if live_result:
                log.result = live_result
            if live_error:
                log.error = live_error

    return _serialize(log)


def _serialize(log) -> dict:
    return {
        "id": str(log.id),
        "celery_task_id": log.celery_task_id,
        "task_name": log.task_name,
        "label": TASK_LABELS.get(log.task_name, log.task_name),
        "status": log.status,
        "params": log.params,
        "result": log.result,
        "error": log.error,
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "updated_at": log.updated_at.isoformat() if log.updated_at else None,
    }
