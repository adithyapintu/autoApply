from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser, UowDep
from app.modules.ai.ats_service import score_resume
from app.modules.ai.company_service import CompanyResearchService
from app.modules.ai.interview_service import InterviewPrepService
from app.modules.ai.salary_service import SalaryEstimationService
from app.modules.ai.services import CoverLetterGenerator, QuestionAnsweringService, ResumeOptimizer

router = APIRouter()


# ── Request models ────────────────────────────────────────────────────────────

class OptimizeResumeRequest(BaseModel):
    job_id: str

class CoverLetterRequest(BaseModel):
    job_id: str
    company_name: str | None = None

class AnswerQuestionRequest(BaseModel):
    question: str

class ATSScoreRequest(BaseModel):
    job_id: str
    parsed_resume: dict | None = None  # if omitted, uses latest parsed resume from DB

class CompanyResearchRequest(BaseModel):
    job_id: str

class SalaryEstimateRequest(BaseModel):
    job_id: str | None = None
    title: str | None = None
    location: str | None = None

class InterviewPrepRequest(BaseModel):
    job_id: str

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/services")
async def list_ai_services() -> list[str]:
    return [
        "resume_optimizer", "cover_letter_generator", "question_answering",
        "ats_scorer", "company_research", "salary_estimation", "interview_prep",
        "resume_parser", "job_matcher",
    ]


@router.post("/optimize-resume")
async def optimize_resume(payload: OptimizeResumeRequest, current_user: CurrentUser, uow: UowDep) -> dict:
    profile = await uow.profiles.find_by_user(current_user.id)
    if not profile:
        from fastapi import HTTPException; raise HTTPException(404, "Profile not found")
    job = await uow.jobs.get(_uuid.UUID(payload.job_id))
    if not job:
        from fastapi import HTTPException; raise HTTPException(404, "Job not found")
    profile_dict = {"skills": [s.name for s in profile.skills], "tech_stacks": profile.tech_stacks, "summary": profile.summary}
    job_dict = {"title": job.title, "description": job.description[:3000]}
    result = await ResumeOptimizer().generate(profile_dict, job_dict)
    return result.model_dump()


@router.post("/cover-letter")
async def generate_cover_letter(payload: CoverLetterRequest, current_user: CurrentUser, uow: UowDep) -> dict:
    profile = await uow.profiles.find_by_user(current_user.id)
    if not profile:
        from fastapi import HTTPException; raise HTTPException(404, "Profile not found")
    job = await uow.jobs.get(_uuid.UUID(payload.job_id))
    if not job:
        from fastapi import HTTPException; raise HTTPException(404, "Job not found")
    profile_dict = {"skills": [s.name for s in profile.skills], "tech_stacks": profile.tech_stacks, "summary": profile.summary}
    job_dict = {"title": job.title, "description": job.description[:3000]}
    company_dict = {"name": payload.company_name or (job.company.name if job.company else "")}
    result = await CoverLetterGenerator().generate(profile_dict, job_dict, company_dict)
    return result.model_dump()


@router.post("/answer-question")
async def answer_question(payload: AnswerQuestionRequest, current_user: CurrentUser, uow: UowDep) -> dict:
    profile = await uow.profiles.find_by_user(current_user.id)
    if not profile:
        from fastapi import HTTPException; raise HTTPException(404, "Profile not found")
    profile_dict = {
        "skills": [s.name for s in profile.skills],
        "experience": [{"company": e.company, "title": e.title, "achievements": e.achievements} for e in profile.experience],
        "projects": [{"name": p.name, "description": p.description} for p in profile.projects],
    }
    result = await QuestionAnsweringService().answer(profile_dict, payload.question)
    return result.model_dump()


@router.post("/ats-score")
async def ats_score(payload: ATSScoreRequest, current_user: CurrentUser, uow: UowDep) -> dict:
    job = await uow.jobs.get(_uuid.UUID(payload.job_id))
    if not job:
        from fastapi import HTTPException; raise HTTPException(404, "Job not found")

    parsed = payload.parsed_resume
    if not parsed:
        # Try to use the latest parsed resume from DB
        resumes = await uow.resumes.list_for_user(current_user.id)
        latest = next((r for r in resumes if r.parsed_json), None)
        if not latest:
            from fastapi import HTTPException; raise HTTPException(400, "No parsed resume found — upload and parse a resume first")
        parsed = latest.parsed_json

    return score_resume(parsed, job.description)


@router.post("/company-research")
async def company_research(payload: CompanyResearchRequest, current_user: CurrentUser, uow: UowDep) -> dict:
    job = await uow.jobs.get(_uuid.UUID(payload.job_id))
    if not job:
        from fastapi import HTTPException; raise HTTPException(404, "Job not found")
    company_name = job.company.name if job.company else "Unknown"
    result = await CompanyResearchService().research(company_name, job.description)
    # Cache in company row if available
    if job.company and not job.company.summary:
        from app.modules.ai.company_service import CompanyResearchService as CRS
        job.company.summary = await CRS().summarise_and_cache(company_name, job.description)
        await uow.commit()
    return result


@router.post("/salary-estimate")
async def salary_estimate(payload: SalaryEstimateRequest, current_user: CurrentUser, uow: UowDep) -> dict:
    title = payload.title
    location = payload.location
    skills: list[str] = []
    years_exp: float | None = None
    remote = False

    if payload.job_id:
        job = await uow.jobs.get(_uuid.UUID(payload.job_id))
        if job:
            title = title or job.title
            location = location or job.location
            remote = job.remote_policy == "remote"

    profile = await uow.profiles.find_by_user(current_user.id)
    if profile:
        skills = profile.tech_stacks + [s.name for s in profile.skills]
        years_exp = float(profile.years_experience) if profile.years_experience else None

    return await SalaryEstimationService().estimate(
        title=title or "Software Engineer",
        location=location,
        skills=skills,
        years_experience=years_exp,
        remote=remote,
    )


@router.post("/interview-prep")
async def interview_prep(payload: InterviewPrepRequest, current_user: CurrentUser, uow: UowDep) -> dict:
    profile = await uow.profiles.find_by_user(current_user.id)
    if not profile:
        from fastapi import HTTPException; raise HTTPException(404, "Profile not found")
    job = await uow.jobs.get(_uuid.UUID(payload.job_id))
    if not job:
        from fastapi import HTTPException; raise HTTPException(404, "Job not found")

    profile_dict = {
        "field": profile.field,
        "tech_stacks": profile.tech_stacks,
        "summary": profile.summary,
        "skills": [{"name": s.name, "category": s.category} for s in profile.skills],
        "experience": [
            {"title": e.title, "company": e.company, "achievements": e.achievements}
            for e in profile.experience
        ],
        "projects": [{"name": p.name, "description": p.description, "skills": p.skills} for p in profile.projects],
    }
    job_dict = {"title": job.title, "description": job.description[:3000]}
    return await InterviewPrepService().generate(profile_dict, job_dict)


@router.get("/semantic-jobs")
async def semantic_job_search(current_user: CurrentUser, uow: UowDep, limit: int = 20) -> list[dict]:
    """Return jobs ranked by vector similarity to the user's profile embedding."""
    profile = await uow.profiles.find_by_user(current_user.id)
    if not profile or profile.embedding is None:
        # Fall back to recency-based
        jobs = await uow.jobs.search(None, limit)
    else:
        jobs = await uow.jobs.search_by_vector(list(profile.embedding), limit)

    return [
        {"id": str(j.id), "title": j.title, "source": j.source,
         "location": j.location, "remote_policy": j.remote_policy, "url": j.url}
        for j in jobs
    ]
