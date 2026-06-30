import httpx

from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class NaukriConnector(JobConnector):
    source = "naukri"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        """
        Naukri.com public job search API (India's largest job board).
        Uses their public search endpoint — no auth required.
        """
        jobs: list[JobDTO] = []
        params: dict[str, str | int] = {
            "noOfResults": min(limit, 20),
            "urlType": "search_by_keyword",
            "searchType": "adv",
            "keyword": query or "",
            "k": query or "",
            "seoKey": "jobs-in-india",
            "src": "jobsearchDesk",
            "latLong": "",
        }
        if location:
            params["l"] = location
            params["li"] = location

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    "https://www.naukri.com/jobapi/v3/search",
                    params=params,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; AutoApply/1.0)",
                        "Accept": "application/json",
                        "SystemCountry": "IN",
                        "Appid": "109",
                        "clientid": "d3skt0p",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                for job in (data.get("jobDetails") or [])[:limit]:
                    job_id = str(job.get("jobId", ""))
                    title = job.get("title", "")
                    company = job.get("companyName", "Unknown")
                    loc = ", ".join(job.get("placeholders", [{}])[0].get("label", "").split(",")[:2]) if job.get("placeholders") else location
                    desc = job.get("jobDescription", "") or f"{title} at {company}"
                    url = job.get("jdURL") or f"https://www.naukri.com/job-listings-{job_id}"
                    salary_raw = job.get("salary", "")

                    if not job_id or not title:
                        continue

                    jobs.append(JobDTO(
                        source=self.source,
                        external_id=job_id,
                        company=company,
                        title=title,
                        description=desc,
                        location=loc or location,
                        url=url,
                    ))
            except Exception:
                pass

        return jobs
