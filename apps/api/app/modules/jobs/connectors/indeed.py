import xml.etree.ElementTree as ET

import httpx

from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class IndeedConnector(JobConnector):
    source = "indeed"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        """
        Indeed public RSS feed — legitimate public endpoint.
        Returns the same jobs shown on indeed.com/jobs search.
        """
        jobs: list[JobDTO] = []
        params: dict[str, str | int] = {
            "q": query or "",
            "limit": min(limit, 25),
            "sort": "date",
        }
        if location:
            params["l"] = location

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            try:
                resp = await client.get(
                    "https://www.indeed.com/rss",
                    params=params,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; AutoApply/1.0)"},
                )
                resp.raise_for_status()
                root = ET.fromstring(resp.text)
                ns = {"atom": "http://www.w3.org/2005/Atom"}

                for item in root.findall(".//item")[:limit]:
                    title = (item.findtext("title") or "").strip()
                    link = (item.findtext("link") or "").strip()
                    description = (item.findtext("description") or "").strip()
                    guid = (item.findtext("guid") or link).strip()

                    # Indeed titles are "Job Title - Company - Location"
                    parts = [p.strip() for p in title.split(" - ")]
                    job_title = parts[0] if parts else title
                    company = parts[1] if len(parts) > 1 else "Unknown"
                    loc = parts[2] if len(parts) > 2 else location

                    if not link:
                        continue

                    jobs.append(JobDTO(
                        source=self.source,
                        external_id=guid,
                        company=company,
                        title=job_title,
                        description=description,
                        location=loc,
                        url=link,
                    ))
            except Exception:
                pass

        return jobs
