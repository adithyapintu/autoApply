from tempfile import NamedTemporaryFile
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.deps import CurrentUser
from app.core.config import settings
from app.modules.resumes.parser import ResumeParser
from app.modules.resumes.schemas import ParsedResume

router = APIRouter()
parser = ResumeParser()


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_resume(current_user: CurrentUser, file: UploadFile = File(...)) -> dict[str, str]:
    if file.content_type not in parser.supported_mime_types:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX resumes are supported")
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Resume exceeds upload limit")
    return {"status": "queued", "user_id": str(current_user.id), "file_name": file.filename or "resume"}


@router.post("/{resume_id}/parse", response_model=ParsedResume)
async def parse_resume(resume_id: UUID, current_user: CurrentUser, file: UploadFile = File(...)) -> ParsedResume:
    with NamedTemporaryFile(delete=True) as temp:
        temp.write(await file.read())
        temp.flush()
        text = parser.extract_text(Path(temp.name), file.content_type or "")
    return parser.parse_baseline(text)
