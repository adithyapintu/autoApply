import asyncio

import httpx

from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class CompanyPageConnector(JobConnector):
    """
    Auto-detect which ATS a company uses and pull jobs from it.
    `query` is a comma-separated list of company slugs or domains,
    e.g. "stripe.com,notion.so,linear" or just "stripe,vercel".
    Tries Greenhouse → Lever → Ashby in order; returns all matches.
    Only accesses officially documented public job board APIs.
    """
    source = "company_pages"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        slugs = [s.strip().rstrip("/").split(".")[-2] if "." in s else s.strip()
                 for s in (query or "").split(",") if s.strip()]
        if not slugs:
            return []

        tasks = [self._detect_and_fetch(slug, limit) for slug in slugs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        jobs: list[JobDTO] = []
        for r in results:
            if isinstance(r, list):
                jobs.extend(r)
        return jobs[:limit]

    async def _detect_and_fetch(self, slug: str, limit: int) -> list[JobDTO]:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            # Try Greenhouse
            jobs = await _try_greenhouse(client, slug, limit)
            if jobs:
                return jobs
            # Try Lever
            jobs = await _try_lever(client, slug, limit)
            if jobs:
                return jobs
            # Try Ashby
            jobs = await _try_ashby(client, slug, limit)
            if jobs:
                return jobs
        return []


async def _try_greenhouse(client: httpx.AsyncClient, slug: str, limit: int) -> list[JobDTO]:
    try:
        resp = await client.get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
        if resp.status_code != 200:
            return []
        return [
            JobDTO(
                source="company_pages",
                external_id=str(j["id"]),
                company=slug,
                title=j["title"],
                description=j.get("content") or "",
                location=(j.get("location") or {}).get("name"),
                url=j["absolute_url"],
            )
            for j in resp.json().get("jobs", [])[:limit]
        ]
    except Exception:
        return []


async def _try_lever(client: httpx.AsyncClient, slug: str, limit: int) -> list[JobDTO]:
    try:
        resp = await client.get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
        if resp.status_code != 200:
            return []
        return [
            JobDTO(
                source="company_pages",
                external_id=j["id"],
                company=slug,
                title=j["text"],
                description=j.get("descriptionPlain") or "",
                location=(j.get("categories") or {}).get("location"),
                url=j["hostedUrl"],
            )
            for j in resp.json()[:limit]
        ]
    except Exception:
        return []


async def _try_ashby(client: httpx.AsyncClient, slug: str, limit: int) -> list[JobDTO]:
    try:
        resp = await client.post(
            f"https://api.ashbyhq.com/posting-api/job-board/{slug}",
            json={},
            headers={"Content-Type": "application/json"},
        )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [
            JobDTO(
                source="company_pages",
                external_id=j["id"],
                company=slug,
                title=j["title"],
                description=j.get("descriptionHtml") or j.get("descriptionPlain") or "",
                location=(j.get("locationName") or j.get("location") or {}).get("name") if isinstance(j.get("locationName"), dict) else j.get("locationName"),
                url=j.get("jobUrl") or f"https://jobs.ashbyhq.com/{slug}/{j['id']}",
            )
            for j in (data.get("jobPostings") or [])[:limit]
        ]
    except Exception:
        return []

