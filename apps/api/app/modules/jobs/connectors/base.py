from abc import ABC, abstractmethod

from app.modules.jobs.schemas import JobDTO


class JobConnector(ABC):
    source: str

    @abstractmethod
    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        """Search provider using official APIs or permitted public feeds."""

