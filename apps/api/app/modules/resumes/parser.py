import json
from pathlib import Path

import docx
import pdfplumber

from app.modules.resumes.schemas import ParsedResume


class ResumeParser:
    supported_mime_types = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def extract_text(self, path: Path, mime_type: str) -> str:
        if mime_type == "application/pdf":
            with pdfplumber.open(path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        if mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            document = docx.Document(path)
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        raise ValueError(f"Unsupported resume MIME type: {mime_type}")

    def parse_baseline(self, text: str) -> ParsedResume:
        """Fast heuristic parse — used as fallback when AI parse is unavailable."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        links = [line for line in lines if line.startswith(("http://", "https://", "www."))]
        likely_skills = [
            token.strip(" ,;")
            for line in lines
            if "skills" in line.lower()
            for token in line.replace("Skills", "").replace("skills", "").split(",")
            if token.strip()
        ]
        return ParsedResume(
            personal_information={"raw_header": lines[:5]},
            skills=likely_skills,
            links=links,
        )

    async def parse_with_ai(self, text: str) -> ParsedResume:
        """AI-powered structured extraction using Groq."""
        from app.modules.ai.services import BaseAIService

        system = (
            "You are a resume parsing expert. "
            "Extract only facts explicitly present in the resume text. "
            "Return JSON with these exact keys: "
            "personal_information (object with name, email, phone, location, linkedin, github), "
            "experience (array of {company, title, start_date, end_date, description, achievements[]}), "
            "education (array of {institution, degree, field, start_date, end_date}), "
            "skills (array of {name, category, proficiency}), "
            "projects (array of {name, description, skills[], links[]}), "
            "certifications (array of {name, issuer, year}), "
            "languages (array of strings), "
            "links (array of strings). "
            "If a field is absent from the resume, return an empty value for that field."
        )

        class _Svc(BaseAIService):
            pass

        raw = await _Svc()._chat(system, f"Resume text:\n\n{text[:8000]}")
        return ParsedResume(
            personal_information=raw.get("personal_information", {}),
            experience=raw.get("experience", []),
            education=raw.get("education", []),
            skills=[s if isinstance(s, dict) else {"name": s, "category": "Other"} for s in raw.get("skills", [])],
            projects=raw.get("projects", []),
            certifications=raw.get("certifications", []),
            languages=raw.get("languages", []),
            links=raw.get("links", []),
        )

