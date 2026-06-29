import httpx

from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class AshbyConnector(JobConnector):
    source = "ashby"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        """
        Ashby's public job board API. Pass org slugs as comma-separated values in `query`.
        """
        orgs = [o.strip() for o in query.split(",") if o.strip()] if query else []
        jobs: list[JobDTO] = []
        async with httpx.AsyncClient(timeout=20) as client:
            for org in orgs:
                try:
                    resp = await client.get(
                        f"https://api.ashbyhq.com/posting-api/job-board/{org}",
                        headers={"Accept": "application/json"},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    for posting in data.get("jobPostings", []):
                        jobs.append(
                            JobDTO(
                                source=self.source,
                                external_id=posting["id"],
                                company=org,
                                title=posting["title"],
                                description=posting.get("descriptionHtml") or posting.get("description", ""),
                                location=posting.get("location"),
                                remote_policy="remote" if posting.get("isRemote") else None,
                                employment_type=posting.get("employmentType"),
                                url=posting["jobUrl"],
                            )
                        )
                except Exception:
                    continue
        return jobs[:limit]

