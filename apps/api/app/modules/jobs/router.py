from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, UowDep
from app.modules.jobs.matcher import JobMatcher
from app.modules.jobs.schemas import MatchReport

router = APIRouter()


@router.get("/search")
async def search_jobs(
    current_user: CurrentUser,
    uow: UowDep,
    q: str | None = Query(default=None),
    limit: int = Query(default=25, le=100),
) -> list[dict]:
    jobs = await uow.jobs.search(q, limit)
    return [
        {
            "id": str(job.id),
            "title": job.title,
            "source": job.source,
            "location": job.location,
            "url": job.url,
        }
        for job in jobs
    ]


@router.post("/{job_id}/match", response_model=MatchReport)
async def match_job(job_id: UUID, current_user: CurrentUser) -> MatchReport:
    return JobMatcher().score(
        profile={"skills": []},
        job={"required_skills": []},
    )

