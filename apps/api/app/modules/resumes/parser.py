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

