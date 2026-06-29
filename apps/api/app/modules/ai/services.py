from pydantic import BaseModel


class AIServiceResult(BaseModel):
    content: dict
    model: str
    prompt_version: str


class BaseAIService:
    prompt_version = "v1"

    def enforce_no_fabrication(self, facts: dict, output: dict) -> dict:
        output["factuality_boundary"] = "candidate_profile_and_job_description_only"
        output["requires_user_review"] = True
        return output


class ResumeOptimizer(BaseAIService):
    async def generate(self, profile: dict, job: dict) -> AIServiceResult:
        return AIServiceResult(
            model="configured-openai-model",
            prompt_version=self.prompt_version,
            content=self.enforce_no_fabrication(
                profile,
                {
                    "ats_score": 0,
                    "keyword_optimization": [],
                    "skills_ordering": [],
                    "project_ordering": [],
                },
            ),
        )


class CoverLetterGenerator(BaseAIService):
    async def generate(self, profile: dict, job: dict, company: dict) -> AIServiceResult:
        return AIServiceResult(
            model="configured-openai-model",
            prompt_version=self.prompt_version,
            content=self.enforce_no_fabrication(profile, {"cover_letter": ""}),
        )


class QuestionAnsweringService(BaseAIService):
    async def answer(self, profile: dict, question: str) -> AIServiceResult:
        return AIServiceResult(
            model="configured-openai-model",
            prompt_version=self.prompt_version,
            content=self.enforce_no_fabrication(profile, {"question": question, "answer": ""}),
        )

