from uuid import UUID

from pydantic import BaseModel, HttpUrl


class JobDTO(BaseModel):
    id: UUID | None = None
    source: str
    external_id: str
    company: str
    title: str
    description: str
    location: str | None = None
    remote_policy: str | None = None
    employment_type: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    visa_sponsorship: bool | None = None
    url: HttpUrl


class MatchReport(BaseModel):
    overall_score: float
    reasons: list[str]
    missing_skills: list[str]
    strengths: list[str]
    recommendation: str

