from fastapi import APIRouter

from app.modules.ai.router import router as ai_router
from app.modules.analytics.router import router as analytics_router
from app.modules.applications.router import router as applications_router
from app.modules.auth.router import router as auth_router
from app.modules.automation.router import router as automation_router
from app.modules.email.router import router as email_router
from app.modules.jobs.router import router as jobs_router
from app.modules.notifications.router import router as notifications_router
from app.modules.profiles.router import router as profiles_router
from app.modules.resumes.router import router as resumes_router
from app.modules.searches.router import router as searches_router

from app.modules.tasks.router import router as tasks_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(resumes_router, prefix="/resumes", tags=["resumes"])
api_router.include_router(profiles_router, prefix="/profiles", tags=["profiles"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(applications_router, prefix="/applications", tags=["applications"])
api_router.include_router(automation_router, prefix="/automation", tags=["automation"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai"])
api_router.include_router(email_router, prefix="/email", tags=["email"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(searches_router, prefix="/searches", tags=["searches"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])

