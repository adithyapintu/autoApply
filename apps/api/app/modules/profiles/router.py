from fastapi import APIRouter

from app.api.deps import CurrentUser, UowDep
from app.modules.profiles.schemas import (
    TECH_FIELDS,
    TECH_STACKS_BY_FIELD,
    ProfileResponse,
    ProfileUpdate,
)

router = APIRouter()


@router.get("/fields")
async def list_fields() -> list[str]:
    """Return all available domain fields (e.g. Backend Engineering)."""
    return TECH_FIELDS


@router.get("/tech-stacks")
async def list_tech_stacks(field: str | None = None) -> dict | list:
    """Return tech stack suggestions. Optionally filtered by field."""
    if field:
        return TECH_STACKS_BY_FIELD.get(field, [])
    return TECH_STACKS_BY_FIELD


@router.get("/me", response_model=ProfileResponse)
async def get_profile(current_user: CurrentUser, uow: UowDep) -> ProfileResponse:
    profile = await uow.profiles.find_by_user(current_user.id)
    if profile is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return ProfileResponse.model_validate(profile)


@router.put("/me", response_model=ProfileResponse)
async def upsert_profile(
    payload: ProfileUpdate,
    current_user: CurrentUser,
    uow: UowDep,
) -> ProfileResponse:
    data = payload.model_dump()
    profile = await uow.profiles.upsert(current_user.id, data)
    await uow.commit()
    refreshed = await uow.profiles.find_by_user(current_user.id)

    # Queue embedding regeneration in the background
    from app.worker import embed_profile
    embed_profile.delay(str(current_user.id))

    return ProfileResponse.model_validate(refreshed)

