import httpx

from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class SmartRecruitersConnector(JobConnector):
    source = "smartrecruiters"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        """
        SmartRecruiters public jobs API.
        Pass company identifiers as comma-separated in `query`, or a keyword search term.
        """
        companies = [c.strip() for c in query.split(",") if c.strip()] if query else []
        jobs: list[JobDTO] = []
        async with httpx.AsyncClient(timeout=20) as client:
            for company in companies:
                try:
                    resp = await client.get(
                        f"https://api.smartrecruiters.com/v1/companies/{company}/postings",
                        params={"limit": min(limit, 100)},
                    )
                    resp.raise_for_status()
                    for posting in resp.json().get("content", []):
                        location_str = None
                        if posting.get("location"):
                            loc = posting["location"]
                            location_str = ", ".join(filter(None, [loc.get("city"), loc.get("country")]))
                        jobs.append(
                            JobDTO(
                                source=self.source,
                                external_id=posting["id"],
                                company=posting.get("company", {}).get("name", company),
                                title=posting["name"],
                                description=posting.get("jobAd", {}).get("sections", {}).get("jobDescription", {}).get("text", ""),
                                location=location_str,
                                remote_policy="remote" if posting.get("typeOfEmployment", {}).get("id") == "TELECOMMUTE" else None,
                                employment_type=posting.get("typeOfEmployment", {}).get("label"),
                                url=f"https://jobs.smartrecruiters.com/{company}/{posting['id']}",
                            )
                        )
                except Exception:
                    continue
        return jobs[:limit]

