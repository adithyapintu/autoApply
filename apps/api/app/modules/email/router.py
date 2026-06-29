from fastapi import APIRouter, status

from app.api.deps import CurrentUser

router = APIRouter()


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
async def sync_email(current_user: CurrentUser) -> dict[str, str]:
    return {"status": "queued", "user_id": str(current_user.id)}


@router.get("/events")
async def list_email_events(current_user: CurrentUser) -> list[dict]:
    return []

