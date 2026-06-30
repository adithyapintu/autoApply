import re

import httpx

from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class LinkedInConnector(JobConnector):
    source = "linkedin"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        """
        LinkedIn guest job search API.
        Returns publicly listed jobs — no auth required.
        Respects LinkedIn's public job board access (same data as linkedin.com/jobs).
        """
        jobs: list[JobDTO] = []
        params: dict[str, str | int] = {
            "keywords": query or "",
            "start": 0,
            "count": min(limit, 25),
        }
        if location:
            params["location"] = location

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",
                    params=params,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; AutoApply/1.0)",
                        "Accept": "text/html,application/xhtml+xml",
                    },
                )
                resp.raise_for_status()
                html = resp.text

                # Each job card has data-entity-urn and basic metadata in the HTML
                job_ids = re.findall(r'data-entity-urn="urn:li:jobPosting:(\d+)"', html)
                titles = re.findall(r'class="base-search-card__title"[^>]*>\s*(.*?)\s*</h3>', html, re.DOTALL)
                companies = re.findall(r'class="base-search-card__subtitle"[^>]*>\s*<[^>]+>\s*(.*?)\s*</a>', html, re.DOTALL)
                locations = re.findall(r'class="job-search-card__location"[^>]*>\s*(.*?)\s*</span>', html, re.DOTALL)

                for i, job_id in enumerate(job_ids[:limit]):
                    title = _clean(titles[i]) if i < len(titles) else "Unknown"
                    company = _clean(companies[i]) if i < len(companies) else "Unknown"
                    loc = _clean(locations[i]) if i < len(locations) else location
                    jobs.append(JobDTO(
                        source=self.source,
                        external_id=job_id,
                        company=company,
                        title=title,
                        description=f"{title} at {company}",
                        location=loc,
                        url=f"https://www.linkedin.com/jobs/view/{job_id}/",
                    ))
            except Exception:
                pass

        return jobs


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()
