from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, UowDep

router = APIRouter()


class SavedSearchCreate(BaseModel):
    name: str = Field(max_length=180)
    source: str = Field(max_length=64)
    query: str = ""
    location: str | None = None
    remote_only: bool = False
    salary_min: int | None = None
    score_threshold: float = 60.0
    interval_hours: int = 24


class SavedSearchResponse(BaseModel):
    id: UUID
    name: str
    source: str
    query: str
    location: str | None
    remote_only: bool
    salary_min: int | None
    score_threshold: float
    interval_hours: int
    is_active: bool
    last_run_at: str | None

    class Config:
        from_attributes = True


@router.get("", response_model=list[SavedSearchResponse])
async def list_saved_searches(current_user: CurrentUser, uow: UowDep) -> list[SavedSearchResponse]:
    searches = await uow.saved_searches.list_for_user(current_user.id)
    return [
        SavedSearchResponse(
            id=s.id, name=s.name, source=s.source, query=s.query,
            location=s.location, remote_only=s.remote_only, salary_min=s.salary_min,
            score_threshold=float(s.score_threshold), interval_hours=s.interval_hours,
            is_active=s.is_active,
            last_run_at=s.last_run_at.isoformat() if s.last_run_at else None,
        )
        for s in searches
    ]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SavedSearchResponse)
async def create_saved_search(
    payload: SavedSearchCreate,
    current_user: CurrentUser,
    uow: UowDep,
) -> SavedSearchResponse:
    ss = await uow.saved_searches.create(current_user.id, payload.model_dump())
    await uow.commit()
    return SavedSearchResponse(
        id=ss.id, name=ss.name, source=ss.source, query=ss.query,
        location=ss.location, remote_only=ss.remote_only, salary_min=ss.salary_min,
        score_threshold=float(ss.score_threshold), interval_hours=ss.interval_hours,
        is_active=ss.is_active, last_run_at=None,
    )


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(search_id: UUID, current_user: CurrentUser, uow: UowDep) -> None:
    ss = await uow.saved_searches.get(search_id)
    if ss is None or ss.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")
    await uow.saved_searches.delete(search_id)
    await uow.commit()


@router.post("/{search_id}/run")
async def run_saved_search(search_id: UUID, current_user: CurrentUser, uow: UowDep) -> dict:
    """Manually trigger a saved search right now."""
    ss = await uow.saved_searches.get(search_id)
    if ss is None or ss.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Search not found")
    from app.worker import process_saved_search
    task = process_saved_search.delay(str(search_id), str(current_user.id))
    return {"status": "queued", "task_id": task.id}
