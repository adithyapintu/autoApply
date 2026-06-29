"""Company research service — summarises a company using Groq from job description context."""
import json

from app.modules.ai.services import BaseAIService


class CompanyResearchService(BaseAIService):
    async def research(self, company_name: str, job_description: str) -> dict:
        system = (
            "You are a company research analyst. "
            "Based only on the company name and job description provided, "
            "generate a concise company profile. "
            "Return JSON with keys: "
            "overview (string — 2 sentences on what the company does), "
            "tech_signals (list[str] — tech stack mentioned or implied), "
            "company_stage (one of: startup | growth | enterprise | unknown), "
            "culture_hints (list[str] — up to 4 culture/work-style signals from the job post), "
            "red_flags (list[str] — any concerns inferred from the job description, or empty list)."
        )
        user_content = (
            f"Company name: {company_name}\n\n"
            f"Job description:\n{job_description[:3500]}"
        )
        return await self._chat(system, user_content)

    async def summarise_and_cache(self, company_name: str, job_description: str) -> str:
        """Return a single-paragraph plain-text summary suitable for storing in Company.summary."""
        raw = await self.research(company_name, job_description)
        overview = raw.get("overview", "")
        stage = raw.get("company_stage", "")
        hints = raw.get("culture_hints", [])
        tech = raw.get("tech_signals", [])
        parts = [overview]
        if stage and stage != "unknown":
            parts.append(f"Stage: {stage}.")
        if tech:
            parts.append(f"Tech signals: {', '.join(tech[:6])}.")
        if hints:
            parts.append(f"Culture: {'; '.join(hints[:3])}.")
        return " ".join(parts)
