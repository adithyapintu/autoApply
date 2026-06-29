from fastapi import APIRouter

from app.api.deps import CurrentUser

router = APIRouter()


@router.get("/summary")
async def summary(current_user: CurrentUser) -> dict[str, float | int]:
    return {
        "applications_this_week": 0,
        "applications_this_month": 0,
        "interview_rate": 0.0,
        "response_rate": 0.0,
        "offer_rate": 0.0,
        "average_match_score": 0.0,
    }


@router.get("/timeline")
async def timeline(current_user: CurrentUser) -> list[dict]:
    return []

