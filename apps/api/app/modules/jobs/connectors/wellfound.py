import httpx

from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class WellfoundConnector(JobConnector):
    source = "wellfound"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        """
        Wellfound (formerly AngelList Talent) public job search.
        Uses the undocumented but publicly accessible job search endpoint.
        `query` is used as a role/keyword search.
        """
        jobs: list[JobDTO] = []
        params: dict = {"q": query or "", "page": 1}
        if location:
            params["location"] = location

        async with httpx.AsyncClient(timeout=20) as client:
            try:
                resp = await client.get(
                    "https://wellfound.com/jobs.json",
                    params=params,
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                data = resp.json()
                for posting in (data.get("jobs") or data.get("data") or [])[:limit]:
                    startup = posting.get("startup") or {}
                    jobs.append(
                        JobDTO(
                            source=self.source,
                            external_id=str(posting.get("id", "")),
                            company=startup.get("name", "Unknown"),
                            title=posting.get("title", ""),
                            description=posting.get("description", ""),
                            location=posting.get("remote", False) and "Remote" or posting.get("location_names", [None])[0],
                            remote_policy="remote" if posting.get("remote") else None,
                            salary_min=posting.get("compensation", {}).get("min"),
                            salary_max=posting.get("compensation", {}).get("max"),
                            url=f"https://wellfound.com/jobs/{posting.get('id', '')}",
                        )
                    )
            except Exception:
                pass
        return jobs

