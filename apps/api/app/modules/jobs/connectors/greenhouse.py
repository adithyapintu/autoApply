import httpx

from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class GreenhouseConnector(JobConnector):
    source = "greenhouse"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        # Greenhouse exposes company-specific job boards. Discovery should supply company tokens.
        return []


async def fetch_company_jobs(company_token: str) -> list[JobDTO]:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"https://boards-api.greenhouse.io/v1/boards/{company_token}/jobs")
        response.raise_for_status()
    jobs = response.json().get("jobs", [])
    return [
        JobDTO(
            source="greenhouse",
            external_id=str(job["id"]),
            company=company_token,
            title=job["title"],
            description=job.get("content") or "",
            location=(job.get("location") or {}).get("name"),
            url=job["absolute_url"],
        )
        for job in jobs
    ]

