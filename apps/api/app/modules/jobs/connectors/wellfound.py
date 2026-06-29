from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class WellfoundConnector(JobConnector):
    source = "wellfound"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        return []

