import hashlib
import tempfile
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response

from app.api.deps import CurrentUser, UowDep
from app.core.config import settings
from app.modules.resumes.latex_service import generate_resume_pdf
from app.modules.resumes.parser import ResumeParser
from app.modules.resumes.schemas import ParsedResume, ResumeResponse

router = APIRouter()
parser = ResumeParser()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_resume(
    current_user: CurrentUser,
    uow: UowDep,
    file: UploadFile = File(...),
) -> dict[str, str]:
    if file.content_type not in parser.supported_mime_types:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX resumes are supported")
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Resume exceeds upload limit")

    sha256 = hashlib.sha256(content).hexdigest()
    storage_key = f"resumes/{current_user.id}/{sha256}/{file.filename}"
    resume = await uow.resumes.create(
        user_id=current_user.id,
        file_name=file.filename or "resume",
        mime_type=file.content_type or "application/octet-stream",
        storage_key=storage_key,
        sha256=sha256,
    )
    await uow.commit()

    # Trigger async AI parsing via Celery
    from app.worker import parse_resume as parse_task
    parse_task.delay(str(resume.id))

    return {"status": "queued", "resume_id": str(resume.id), "file_name": resume.file_name}


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(current_user: CurrentUser, uow: UowDep) -> list[ResumeResponse]:
    resumes = await uow.resumes.list_for_user(current_user.id)
    return [ResumeResponse.model_validate(r) for r in resumes]


@router.post("/{resume_id}/parse", response_model=ParsedResume)
async def parse_resume_endpoint(
    resume_id: UUID,
    current_user: CurrentUser,
    uow: UowDep,
    file: UploadFile = File(...),
) -> ParsedResume:
    with tempfile.NamedTemporaryFile(delete=True) as temp:
        content = await file.read()
        temp.write(content)
        temp.flush()
        text = parser.extract_text(Path(temp.name), file.content_type or "")
    parsed = await parser.parse_with_ai(text)
    await uow.resumes.update_parsed(resume_id, parsed.model_dump())
    await uow.commit()
    return parsed


@router.post("/generate", response_class=Response)
async def generate_resume(
    current_user: CurrentUser,
    uow: UowDep,
    tech_stacks: list[str] = Query(default=[]),
) -> Response:
    """Generate a LaTeX-compiled PDF resume from the user's profile."""
    profile = await uow.profiles.find_by_user(current_user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found — complete your profile first")

    # Build a flat dict the LaTeX service understands
    profile_dict = {
        "full_name": profile.user.full_name if profile.user else "",
        "field": profile.field,
        "tech_stacks": tech_stacks or profile.tech_stacks,
        "summary": profile.summary,
        "skills": [
            {"name": s.name, "category": s.category, "proficiency": s.proficiency}
            for s in profile.skills
        ],
        "experience": [
            {
                "company": e.company, "title": e.title,
                "start_date": str(e.start_date) if e.start_date else "",
                "end_date": str(e.end_date) if e.end_date else "",
                "description": e.description or "",
                "achievements": e.achievements,
            }
            for e in profile.experience
        ],
        "education": [
            {
                "institution": edu.institution, "degree": edu.degree,
                "field": edu.field,
                "start_date": str(edu.start_date) if edu.start_date else "",
                "end_date": str(edu.end_date) if edu.end_date else "",
            }
            for edu in profile.education
        ],
        "projects": [
            {"name": p.name, "description": p.description or "", "skills": p.skills, "links": p.links}
            for p in profile.projects
        ],
        "personal_information": {},
    }

    try:
        pdf_bytes = generate_resume_pdf(profile_dict, tech_stacks or None)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=resume.pdf"},
    )
