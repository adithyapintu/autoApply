import json

from groq import AsyncGroq
from pydantic import BaseModel

from app.core.config import settings

_NO_FABRICATION_SUFFIX = (
    "\n\nIMPORTANT: Only use facts explicitly provided in the input. "
    "Never invent experience, skills, metrics, dates, certifications, degrees, "
    "employers, or projects. Return valid JSON only."
)


class AIServiceResult(BaseModel):
    content: dict
    model: str
    prompt_version: str


class BaseAIService:
    prompt_version = "v1"

    def _client(self) -> AsyncGroq:
        return AsyncGroq(api_key=settings.groq_api_key)

    async def _chat(self, system: str, user_content: str) -> dict:
        completion = await self._client().chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system + _NO_FABRICATION_SUFFIX},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return json.loads(completion.choices[0].message.content)

    def enforce_no_fabrication(self, facts: dict, output: dict) -> dict:
        output["factuality_boundary"] = "candidate_profile_and_job_description_only"
        output["requires_user_review"] = True
        return output


class ResumeOptimizer(BaseAIService):
    async def generate(self, profile: dict, job: dict) -> AIServiceResult:
        system = (
            "You are an ATS resume optimization expert. "
            "Reorder and emphasize truthful information already present in the candidate profile. "
            "Return JSON with keys: ats_score (float 0-100), keyword_optimization (list[str]), "
            "skills_ordering (list[str]), project_ordering (list[str])."
        )
        raw = await self._chat(system, f"Profile:\n{json.dumps(profile)}\n\nJob:\n{json.dumps(job)}")
        content = self.enforce_no_fabrication(profile, {
            "ats_score": raw.get("ats_score", 0),
            "keyword_optimization": raw.get("keyword_optimization", []),
            "skills_ordering": raw.get("skills_ordering", []),
            "project_ordering": raw.get("project_ordering", []),
        })
        return AIServiceResult(model=settings.groq_model, prompt_version=self.prompt_version, content=content)


class CoverLetterGenerator(BaseAIService):
    async def generate(self, profile: dict, job: dict, company: dict) -> AIServiceResult:
        system = (
            "You are a professional cover letter writer. "
            "Write a concise 3-paragraph cover letter grounded only in the provided profile, "
            "job description, and company information. "
            "Replace any missing personalization with [MISSING: detail] — never invent facts. "
            "Return JSON with key: cover_letter (string)."
        )
        user_content = (
            f"Profile:\n{json.dumps(profile)}\n\n"
            f"Job:\n{json.dumps(job)}\n\n"
            f"Company:\n{json.dumps(company)}"
        )
        raw = await self._chat(system, user_content)
        content = self.enforce_no_fabrication(profile, {"cover_letter": raw.get("cover_letter", "")})
        return AIServiceResult(model=settings.groq_model, prompt_version=self.prompt_version, content=content)


class QuestionAnsweringService(BaseAIService):
    async def answer(self, profile: dict, question: str) -> AIServiceResult:
        system = (
            "You are a job application assistant. "
            "Answer the application question using only facts from the candidate profile. "
            "Behavioral answers must be traceable to specific experience, projects, or achievements. "
            "If there is insufficient information, set answer to null and provide a follow_up_question. "
            "Return JSON with keys: answer (string|null), follow_up_question (string|null)."
        )
        raw = await self._chat(system, f"Profile:\n{json.dumps(profile)}\n\nQuestion: {question}")
        content = self.enforce_no_fabrication(profile, {
            "question": question,
            "answer": raw.get("answer"),
            "follow_up_question": raw.get("follow_up_question"),
        })
        return AIServiceResult(model=settings.groq_model, prompt_version=self.prompt_version, content=content)

