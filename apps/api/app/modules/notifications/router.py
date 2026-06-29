from fastapi import APIRouter, status

from app.api.deps import CurrentUser

router = APIRouter()


@router.get("")
async def list_notifications(current_user: CurrentUser) -> list[dict]:
    return []


@router.post("/test", status_code=status.HTTP_202_ACCEPTED)
async def test_notification(current_user: CurrentUser) -> dict[str, str]:
    return {"status": "queued", "user_id": str(current_user.id)}

