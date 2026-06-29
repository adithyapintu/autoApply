from uuid import UUID

from pydantic import BaseModel


class ParsedResume(BaseModel):
    personal_information: dict = {}
    experience: list[dict] = []
    skills: list[str] = []
    projects: list[dict] = []
    certifications: list[dict] = []
    education: list[dict] = []
    languages: list[str] = []
    links: list[str] = []


class ResumeResponse(BaseModel):
    id: UUID
    file_name: str
    mime_type: str
    parsed_json: dict | None

