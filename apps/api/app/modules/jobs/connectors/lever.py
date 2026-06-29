import httpx

from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class LeverConnector(JobConnector):
    source = "lever"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        """
        Lever's public posting API requires a company slug.
        Pass company slugs as comma-separated values in `query`, e.g. "netflix,stripe".
        """
        companies = [c.strip() for c in query.split(",") if c.strip()] if query else []
        jobs: list[JobDTO] = []
        async with httpx.AsyncClient(timeout=20) as client:
            for company in companies:
                try:
                    resp = await client.get(
                        f"https://api.lever.co/v0/postings/{company}",
                        params={"mode": "json", "limit": limit},
                    )
                    resp.raise_for_status()
                    for posting in resp.json():
                        jobs.append(
                            JobDTO(
                                source=self.source,
                                external_id=posting["id"],
                                company=posting.get("categories", {}).get("team", company),
                                title=posting["text"],
                                description=posting.get("descriptionPlain") or posting.get("description", ""),
                                location=posting.get("categories", {}).get("location"),
                                remote_policy="remote" if "remote" in posting.get("categories", {}).get("location", "").lower() else None,
                                url=posting["hostedUrl"],
                            )
                        )
                except Exception:
                    continue
        return jobs[:limit]


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

