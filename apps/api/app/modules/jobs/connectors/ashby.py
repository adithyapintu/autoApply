from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class AshbyConnector(JobConnector):
    source = "ashby"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        return []

