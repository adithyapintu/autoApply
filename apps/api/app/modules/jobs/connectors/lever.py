import httpx

from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class LeverConnector(JobConnector):
    source = "lever"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        return []


async def fetch_company_jobs(company_slug: str) -> list[JobDTO]:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"https://api.lever.co/v0/postings/{company_slug}?mode=json")
        response.raise_for_status()
    return [
        JobDTO(
            source="lever",
            external_id=job["id"],
            company=company_slug,
            title=job["text"],
            description=job.get("descriptionPlain") or "",
            location=(job.get("categories") or {}).get("location"),
            employment_type=(job.get("categories") or {}).get("commitment"),
            url=job["hostedUrl"],
        )
        for job in response.json()
    ]

