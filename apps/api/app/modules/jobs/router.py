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
            "remote_policy": job.remote_policy,
            "employment_type": job.employment_type,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "url": job.url,
        }
        for job in jobs
    ]


@router.post("/{job_id}/match", response_model=MatchReport)
async def match_job(job_id: UUID, current_user: CurrentUser, uow: UowDep) -> MatchReport:
    job = await uow.jobs.get(job_id)
    if job is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")

    profile = await uow.profiles.find_by_user(current_user.id)
    profile_dict = {"skills": [s.name for s in profile.skills] if profile else []}
    job_dict = {"required_skills": job.tech_stacks if hasattr(job, "tech_stacks") else []}
    return JobMatcher().score(profile_dict, job_dict)


@router.post("/discover")
async def discover_jobs(
    current_user: CurrentUser,
    uow: UowDep,
    source: str = Query(...),
    query: str = Query(default=""),
    location: str | None = Query(default=None),
) -> dict[str, str]:
    """Queue a background job discovery task for the given source."""
    from app.worker import discover_jobs as discover_task
    task = discover_task.delay(str(current_user.id), source, query, location)
    await uow.task_logs.create(
        user_id=current_user.id,
        celery_task_id=task.id,
        task_name="discover_jobs",
        params={"source": source, "query": query, "location": location},
    )
    await uow.commit()
    return {"status": "queued", "task_id": task.id, "source": source}


@router.get("/{job_id}")
async def get_job(job_id: UUID, current_user: CurrentUser, uow: UowDep) -> dict:
    job = await uow.jobs.get(job_id)
    if job is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": str(job.id),
        "title": job.title,
        "description": job.description,
        "source": job.source,
        "location": job.location,
        "remote_policy": job.remote_policy,
        "employment_type": job.employment_type,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "visa_sponsorship": job.visa_sponsorship,
        "url": job.url,
        "company": job.company.name if job.company else None,
        "company_summary": job.company.summary if job.company else None,
        "has_embedding": job.embedding is not None,
    }
