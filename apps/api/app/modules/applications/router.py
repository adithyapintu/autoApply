import csv
import io
import json
from uuid import UUID

from fastapi import APIRouter, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import CurrentUser, UowDep

router = APIRouter()

REFERRAL_CHANNELS = ["LinkedIn", "Employee Referral", "Email", "In-person", "Twitter/X", "Other"]


class CreateApplicationRequest(BaseModel):
    job_id: UUID
    referred_by: str | None = None
    referral_channel: str | None = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: CreateApplicationRequest,
    current_user: CurrentUser,
    uow: UowDep,
) -> dict:
    application = await uow.applications.create(
        current_user.id,
        payload.job_id,
        referred_by=payload.referred_by,
        referral_channel=payload.referral_channel,
    )
    await uow.commit()
    return {
        "id": str(application.id),
        "status": application.status,
        "referred_by": application.referred_by,
    }


@router.get("")
async def list_applications(current_user: CurrentUser, uow: UowDep) -> list[dict]:
    applications = await uow.applications.list_for_user(current_user.id)
    return [
        {
            "id": str(item.id),
            "status": item.status,
            "job_id": str(item.job_id),
            "match_score": float(item.match_score) if item.match_score else None,
            "referred_by": item.referred_by,
            "referral_channel": item.referral_channel,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in applications
    ]


@router.patch("/{application_id}/status")
async def update_application_status(
    application_id: UUID,
    status: str = Query(...),
    current_user: CurrentUser = None,
    uow: UowDep = None,
) -> dict:
    app = await uow.applications.get(application_id)
    if app is None or app.user_id != current_user.id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Application not found")
    await uow.applications.update_status(application_id, status)
    await uow.commit()
    return {"id": str(application_id), "status": status}


@router.get("/export")
async def export_applications(
    current_user: CurrentUser,
    uow: UowDep,
    format: str = Query(default="csv", regex="^(csv|json)$"),
) -> StreamingResponse:
    """Export application history as CSV or full GDPR JSON bundle."""
    applications = await uow.applications.list_for_user(current_user.id)

    if format == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "id", "job_id", "status", "match_score", "referred_by",
            "referral_channel", "created_at", "applied_at",
        ])
        writer.writeheader()
        for app in applications:
            writer.writerow({
                "id": str(app.id),
                "job_id": str(app.job_id),
                "status": app.status,
                "match_score": float(app.match_score) if app.match_score else "",
                "referred_by": app.referred_by or "",
                "referral_channel": app.referral_channel or "",
                "created_at": app.created_at.isoformat() if app.created_at else "",
                "applied_at": app.applied_at.isoformat() if app.applied_at else "",
            })
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=applications.csv"},
        )

    # JSON GDPR portability bundle
    profile = await uow.profiles.find_by_user(current_user.id)
    resumes = await uow.resumes.list_for_user(current_user.id)
    user = await uow.users.find_by_id(current_user.id)

    bundle = {
        "export_version": "1.0",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
        "profile": {
            "field": profile.field if profile else None,
            "tech_stacks": profile.tech_stacks if profile else [],
            "seniority": profile.seniority if profile else None,
            "summary": profile.summary if profile else None,
            "skills": [{"name": s.name, "category": s.category} for s in (profile.skills if profile else [])],
        },
        "resumes": [{"file_name": r.file_name, "created_at": r.created_at.isoformat()} for r in resumes],
        "applications": [
            {
                "id": str(a.id),
                "job_id": str(a.job_id),
                "status": a.status,
                "match_score": float(a.match_score) if a.match_score else None,
                "referred_by": a.referred_by,
                "referral_channel": a.referral_channel,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "applied_at": a.applied_at.isoformat() if a.applied_at else None,
                "notes": a.notes,
                "interview_stages": a.interview_stages,
                "offer_details": a.offer_details,
            }
            for a in applications
        ],
    }
    json_bytes = json.dumps(bundle, indent=2).encode()
    return StreamingResponse(
        iter([json_bytes]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=autoapply-export.json"},
    )

