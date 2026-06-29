from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import CurrentUser

router = APIRouter()


class ProfileResponse(BaseModel):
    user_id: str
    years_experience: float | None = None
    primary_skills: list[str] = []
    secondary_skills: list[str] = []
    seniority: str | None = None
    domain_expertise: list[str] = []
    preferred_roles: list[str] = []
    industry: list[str] = []
    ats_keywords: list[str] = []


@router.get("/me", response_model=ProfileResponse)
async def get_profile(current_user: CurrentUser) -> ProfileResponse:
    return ProfileResponse(user_id=str(current_user.id))


@router.post("/generate", response_model=ProfileResponse)
async def generate_profile(current_user: CurrentUser) -> ProfileResponse:
    return ProfileResponse(user_id=str(current_user.id))

