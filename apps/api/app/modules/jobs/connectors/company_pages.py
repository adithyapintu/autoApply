from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class CompanyPageConnector(JobConnector):
    source = "company_pages"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        # Only use this when robots.txt, terms, and user/customer authorization permit crawling.
        return []

