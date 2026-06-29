from fastapi import APIRouter

router = APIRouter()


@router.get("/services")
async def list_ai_services() -> list[str]:
    return [
        "resume_parser",
        "job_matcher",
        "resume_optimizer",
        "cover_letter_generator",
        "question_answering",
        "application_summarizer",
        "skill_extractor",
        "company_summarizer",
        "salary_estimation",
        "interview_preparation",
    ]

