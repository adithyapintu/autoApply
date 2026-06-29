import re

import httpx

from app.modules.jobs.connectors.base import JobConnector
from app.modules.jobs.schemas import JobDTO


class WorkdayConnector(JobConnector):
    source = "workday"

    async def search(self, query: str, location: str | None = None, limit: int = 25) -> list[JobDTO]:
        """
        Workday job boards expose a JSON API at:
          https://{tenant}.wd{n}.myworkday.com/wday/cxs/{tenant}/{board}/jobs
        Pass tenant URLs as comma-separated values in `query`, e.g.:
          "netflix/careers,stripe/careers"
        Format: "{tenant}/{board}" - the connector builds the Workday API URL automatically.
        """
        entries = [e.strip() for e in query.split(",") if e.strip()] if query else []
        jobs: list[JobDTO] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for entry in entries:
                parts = entry.split("/")
                if len(parts) < 2:
                    continue
                tenant, board = parts[0], parts[1]
                # Try common Workday domain patterns
                for subdomain in [f"https://{tenant}.wd5.myworkday.com", f"https://{tenant}.wd3.myworkday.com"]:
                    try:
                        url = f"{subdomain}/wday/cxs/{tenant}/{board}/jobs"
                        resp = await client.post(
                            url,
                            json={"limit": min(limit, 20), "offset": 0, "searchText": location or ""},
                            headers={"Content-Type": "application/json", "Accept": "application/json"},
                            timeout=15,
                        )
                        if resp.status_code not in (200, 201):
                            continue
                        data = resp.json()
                        for posting in (data.get("jobPostings") or []):
                            external_id = posting.get("bulletFields", [None])[0] or posting.get("title", "")
                            jobs.append(
                                JobDTO(
                                    source=self.source,
                                    external_id=str(posting.get("externalPath") or external_id),
                                    company=tenant,
                                    title=posting.get("title", ""),
                                    description=posting.get("locationsText", ""),
                                    location=posting.get("locationsText"),
                                    remote_policy="remote" if "remote" in posting.get("locationsText", "").lower() else None,
                                    url=f"{subdomain}{posting.get('externalPath', '')}",
                                )
                            )
                        break
                    except Exception:
                        continue
        return jobs[:limit]

