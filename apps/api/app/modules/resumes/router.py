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

    # Extract raw text immediately so the async worker has something to parse
    initial_parsed: dict | None = None
    suffix = Path(file.filename or "resume.pdf").suffix or ".pdf"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        raw_text = parser.extract_text(tmp_path, file.content_type or "")
        if raw_text.strip():
            initial_parsed = {"raw_text": raw_text}
    except Exception:
        pass
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

    resume = await uow.resumes.create(
        user_id=current_user.id,
        file_name=file.filename or "resume",
        mime_type=file.content_type or "application/octet-stream",
        storage_key=storage_key,
        sha256=sha256,
        parsed_json=initial_parsed,
    )
    await uow.commit()

    # Trigger async AI parsing via Celery
    from app.worker import parse_resume as parse_task
    task = parse_task.delay(str(resume.id))
    await uow.task_logs.create(
        user_id=current_user.id,
        celery_task_id=task.id,
        task_name="parse_resume",
        params={"resume_id": str(resume.id), "file_name": resume.file_name},
    )
    await uow.commit()

    return {"status": "queued", "resume_id": str(resume.id), "file_name": resume.file_name}


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(current_user: CurrentUser, uow: UowDep) -> list[ResumeResponse]:
    resumes = await uow.resumes.list_for_user(current_user.id)
    return [ResumeResponse.model_validate(r) for r in resumes]


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(resume_id: UUID, current_user: CurrentUser, uow: UowDep) -> None:
    resume = await uow.resumes.get(resume_id)
    if resume is None or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")
    await uow.resumes.delete(resume_id)
    await uow.commit()


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
