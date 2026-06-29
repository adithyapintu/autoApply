import base64
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl

from app.api.deps import CurrentUser, UowDep

router = APIRouter()


class CreateAutomationTaskRequest(BaseModel):
    application_id: UUID
    target_url: HttpUrl
    site_adapter: str = "generic"
    answers: dict[str, str] = {}


class AutomationTaskResponse(BaseModel):
    id: UUID
    application_id: UUID
    status: str
    site_adapter: str
    checkpoint: dict | None
    screenshots: list[str]
    error: str | None


def _task_to_response(task) -> AutomationTaskResponse:
    return AutomationTaskResponse(
        id=task.id,
        application_id=task.application_id,
        status=task.status,
        site_adapter=task.site_adapter,
        checkpoint=task.checkpoint,
        screenshots=task.screenshots or [],
        error=task.error,
    )


@router.get("/tasks", response_model=list[AutomationTaskResponse])
async def list_tasks(current_user: CurrentUser, uow: UowDep) -> list[AutomationTaskResponse]:
    from sqlalchemy import select
    from app.db import models
    result = await uow.session.execute(
        select(models.AutomationTask)
        .join(models.Application, models.AutomationTask.application_id == models.Application.id)
        .where(models.Application.user_id == current_user.id)
        .order_by(models.AutomationTask.created_at.desc())
        .limit(50)
    )
    return [_task_to_response(t) for t in result.scalars().all()]


@router.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
async def create_task(
    payload: CreateAutomationTaskRequest,
    current_user: CurrentUser,
    uow: UowDep,
) -> dict[str, str]:
    from app.db import models

    # Verify the application belongs to this user
    app = await uow.applications.get(payload.application_id)
    if app is None or app.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Application not found")

    db_task = models.AutomationTask(
        application_id=payload.application_id,
        status="pending",
        site_adapter=payload.site_adapter,
        checkpoint=None,
    )
    uow.session.add(db_task)
    await uow.commit()

    from app.worker import run_automation
    run_automation.delay(str(db_task.id), str(payload.target_url), payload.site_adapter, payload.answers)

    return {
        "status": "queued",
        "task_id": str(db_task.id),
        "safety": "automation will pause before final submission for your review",
    }


@router.get("/tasks/{task_id}", response_model=AutomationTaskResponse)
async def get_task(task_id: UUID, current_user: CurrentUser, uow: UowDep) -> AutomationTaskResponse:
    from app.db import models
    task = await uow.session.get(models.AutomationTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    app = await uow.applications.get(task.application_id)
    if app is None or app.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return _task_to_response(task)


@router.get("/tasks/{task_id}/screenshot")
async def get_screenshot(task_id: UUID, current_user: CurrentUser, uow: UowDep) -> dict:
    """Return the approval checkpoint screenshot as base64."""
    from app.db import models
    task = await uow.session.get(models.AutomationTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    app = await uow.applications.get(task.application_id)
    if app is None or app.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    screenshots = task.screenshots or []
    if not screenshots:
        return {"screenshot": None}
    path = Path(screenshots[0])
    if not path.exists():
        return {"screenshot": None}
    data = base64.b64encode(path.read_bytes()).decode()
    return {"screenshot": f"data:image/png;base64,{data}"}


@router.post("/tasks/{task_id}/approve")
async def approve_task(task_id: UUID, current_user: CurrentUser, uow: UowDep) -> dict[str, str]:
    from app.db import models
    task = await uow.session.get(models.AutomationTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    app = await uow.applications.get(task.application_id)
    if app is None or app.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if task.status != "awaiting_approval":
        raise HTTPException(status_code=400, detail=f"Task is '{task.status}', not awaiting approval")

    task.status = "approved"
    await uow.commit()

    from app.worker import submit_application
    submit_application.delay(str(task_id))
    return {"status": "approved_queued_for_submit", "task_id": str(task_id)}


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: UUID, current_user: CurrentUser, uow: UowDep) -> dict[str, str]:
    from app.db import models
    task = await uow.session.get(models.AutomationTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    app = await uow.applications.get(task.application_id)
    if app is None or app.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    task.status = "cancelled"
    await uow.commit()
    return {"status": "cancelled", "task_id": str(task_id)}

