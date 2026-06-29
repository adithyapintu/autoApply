from uuid import UUID

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.api.deps import CurrentUser, UowDep

router = APIRouter()


class CreateApplicationRequest(BaseModel):
    job_id: UUID


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_application(payload: CreateApplicationRequest, current_user: CurrentUser, uow: UowDep) -> dict:
    application = await uow.applications.create(current_user.id, payload.job_id)
    await uow.commit()
    return {"id": str(application.id), "status": application.status}


@router.get("")
async def list_applications(current_user: CurrentUser, uow: UowDep) -> list[dict]:
    applications = await uow.applications.list_for_user(current_user.id)
    return [{"id": str(item.id), "status": item.status, "job_id": str(item.job_id)} for item in applications]

