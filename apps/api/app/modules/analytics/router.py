from collections import defaultdict
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter

from app.api.deps import CurrentUser, UowDep

router = APIRouter()

KNOWN_SKILLS = [
    "Python", "JavaScript", "TypeScript", "Go", "Java", "Rust", "C#", "Ruby",
    "React", "Next.js", "Vue.js", "Angular", "Svelte",
    "FastAPI", "Django", "Flask", "Express", "NestJS", "Spring Boot",
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Kafka",
    "Docker", "Kubernetes", "AWS", "GCP", "Azure",
    "Node.js", "GraphQL", "gRPC", "Terraform", "Linux", "CI/CD",
    "TensorFlow", "PyTorch", "scikit-learn", "pandas",
    "React Native", "Flutter", "Swift", "Kotlin",
]

ORDERED_STAGES = ["draft", "applied", "phone_screen", "interview", "offer", "rejected"]


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


@router.get("/funnel")
async def funnel(current_user: CurrentUser, uow: UowDep) -> dict:
    apps = await uow.applications.list_for_user(current_user.id)

    counts: dict[str, int] = {s: 0 for s in ORDERED_STAGES}
    for a in apps:
        key = a.status if a.status in counts else "draft"
        counts[key] += 1

    total = len(apps)

    # Median days from application creation to first non-applied response
    response_times: list[int] = []
    for a in apps:
        if a.applied_at and a.status not in ("draft", "applied") and a.created_at:
            delta = (a.applied_at - a.created_at).days
            if 0 <= delta <= 365:
                response_times.append(delta)
    response_times.sort()
    median_resp = response_times[len(response_times) // 2] if response_times else None

    # Match-score correlation
    high = [a for a in apps if a.match_score and float(a.match_score) >= 70]
    low = [a for a in apps if a.match_score and float(a.match_score) < 70]

    def _resp_rate(subset: list) -> float:
        if not subset:
            return 0.0
        return round(sum(1 for a in subset if a.status not in ("draft", "applied")) / len(subset) * 100, 1)

    return {
        "stages": [{"stage": s, "count": counts[s]} for s in ORDERED_STAGES],
        "total": total,
        "median_days_to_response": median_resp,
        "match_score_correlation": {
            "high_score_response_rate": _resp_rate(high),
            "low_score_response_rate": _resp_rate(low),
            "high_score_count": len(high),
            "low_score_count": len(low),
        },
    }


@router.get("/by-source")
async def by_source(current_user: CurrentUser, uow: UowDep) -> list[dict]:
    pairs = await uow.applications.list_with_jobs(current_user.id)

    data: dict[str, dict] = defaultdict(lambda: {
        "total": 0, "responses": 0, "interviews": 0, "offers": 0, "scores": []
    })

    for app, job in pairs:
        src = job.source if job else "unknown"
        d = data[src]
        d["total"] += 1
        if app.status not in ("draft", "applied"):
            d["responses"] += 1
        if app.status in ("phone_screen", "interview", "offer"):
            d["interviews"] += 1
        if app.status == "offer":
            d["offers"] += 1
        if app.match_score:
            d["scores"].append(float(app.match_score))

    result = []
    for src, d in sorted(data.items(), key=lambda x: -x[1]["total"]):
        t = d["total"]
        s = d["scores"]
        result.append({
            "source": src,
            "total": t,
            "response_rate": round(d["responses"] / t * 100, 1) if t else 0.0,
            "interview_rate": round(d["interviews"] / t * 100, 1) if t else 0.0,
            "offer_rate": round(d["offers"] / t * 100, 1) if t else 0.0,
            "avg_match_score": round(sum(s) / len(s), 1) if s else None,
        })
    return result


@router.get("/velocity")
async def velocity(current_user: CurrentUser, uow: UowDep) -> dict:
    apps = await uow.applications.list_for_user(current_user.id)
    now = datetime.now(UTC)

    daily: dict[str, int] = {
        (now - timedelta(days=i)).strftime("%Y-%m-%d"): 0 for i in range(29, -1, -1)
    }
    for a in apps:
        if a.created_at:
            day = a.created_at.strftime("%Y-%m-%d")
            if day in daily:
                daily[day] += 1

    daily_list = [{"date": d, "count": c} for d, c in daily.items()]
    rolling_7 = round(sum(daily_list[-i]["count"] for i in range(1, 8)) / 7, 1) if len(daily_list) >= 7 else 0.0

    total = len(apps)
    low_match = [a for a in apps if a.match_score and float(a.match_score) < 50]
    low_match_pct = round(len(low_match) / total * 100) if total else 0

    warnings: list[str] = []
    if total > 0 and rolling_7 < 1:
        warnings.append("Application rate is low — aim for at least 5 per week.")
    if rolling_7 > 20:
        warnings.append("High volume detected — consider targeting higher-match roles.")
    if low_match_pct > 50:
        warnings.append(f"{low_match_pct}% of applications score below 50 — update your profile to improve matching.")

    offers = sum(1 for a in apps if a.status == "offer")
    offer_rate = offers / total if total > 0 else 0.02
    suggested = min(200, max(10, round(2 / max(offer_rate, 0.01))))

    return {
        "daily": daily_list,
        "rolling_7day_avg": rolling_7,
        "total_last_30_days": sum(d["count"] for d in daily_list),
        "suggested_monthly_target": suggested,
        "warnings": warnings,
    }


@router.get("/market")
async def market(current_user: CurrentUser, uow: UowDep) -> dict:
    descriptions = await uow.jobs.get_descriptions(limit=500)
    all_text = " ".join(descriptions).lower()

    skill_counts = {s: all_text.count(s.lower()) for s in KNOWN_SKILLS}
    top = sorted(((s, c) for s, c in skill_counts.items() if c > 0), key=lambda x: -x[1])[:20]

    profile = await uow.profiles.find_by_user(current_user.id)
    user_skills: set[str] = set()
    if profile:
        user_skills = {s.name.lower() for s in profile.skills} | {ts.lower() for ts in profile.tech_stacks}

    return {
        "top_skills": [{"skill": s, "demand": c, "in_profile": s.lower() in user_skills} for s, c in top],
        "total_jobs_analyzed": len(descriptions),
        "profile_skill_count": len(user_skills),
    }

