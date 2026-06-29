from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel, HttpUrl

from app.api.deps import CurrentUser

router = APIRouter()


class CreateAutomationTaskRequest(BaseModel):
    application_id: UUID
    target_url: HttpUrl
    site_adapter: str = "generic"


@router.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
async def create_task(payload: CreateAutomationTaskRequest, current_user: CurrentUser) -> dict[str, str]:
    return {
        "status": "queued",
        "application_id": str(payload.application_id),
        "safety": "automation will pause before final submission",
    }


@router.post("/tasks/{task_id}/approve")
async def approve_task(task_id: UUID, current_user: CurrentUser) -> dict[str, str]:
    return {"status": "approved_for_submit", "task_id": str(task_id)}


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: UUID, current_user: CurrentUser) -> dict[str, str]:
    return {"status": "cancelled", "task_id": str(task_id)}

