from datetime import UTC, datetime, timedelta

from fastapi import APIRouter

from app.api.deps import CurrentUser, UowDep

router = APIRouter()


@router.get("/summary")
async def summary(current_user: CurrentUser, uow: UowDep) -> dict[str, float | int]:
    apps = await uow.applications.list_for_user(current_user.id)
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    this_week = sum(1 for a in apps if a.created_at and a.created_at >= week_ago)
    this_month = sum(1 for a in apps if a.created_at and a.created_at >= month_ago)
    total = len(apps)
    interviews = sum(1 for a in apps if a.status in ("phone_screen", "interview", "offer"))
    responses = sum(1 for a in apps if a.status not in ("draft", "applied"))
    offers = sum(1 for a in apps if a.status == "offer")
    scores = [float(a.match_score) for a in apps if a.match_score is not None]

    return {
        "applications_this_week": this_week,
        "applications_this_month": this_month,
        "interview_rate": round((interviews / total * 100) if total else 0.0, 1),
        "response_rate": round((responses / total * 100) if total else 0.0, 1),
        "offer_rate": round((offers / total * 100) if total else 0.0, 1),
        "average_match_score": round(sum(scores) / len(scores), 1) if scores else 0.0,
    }


@router.get("/timeline")
async def timeline(current_user: CurrentUser, uow: UowDep) -> list[dict]:
    apps = await uow.applications.list_for_user(current_user.id)
    return [
        {"date": str(a.created_at.date()) if a.created_at else None, "status": a.status}
        for a in apps
    ]

