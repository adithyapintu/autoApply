"""Salary estimation service — uses Groq to estimate compensation ranges."""
from app.modules.ai.services import BaseAIService


class SalaryEstimationService(BaseAIService):
    async def estimate(
        self,
        title: str,
        location: str | None,
        skills: list[str],
        years_experience: float | None,
        remote: bool = False,
    ) -> dict:
        system = (
            "You are a compensation analyst with deep knowledge of current tech industry salaries "
            "across the US, EU, and remote-first markets. "
            "Estimate realistic annual salary ranges based on the provided role details. "
            "Base your estimate on current market data (2025-2026). "
            "Return JSON with keys: "
            "min_usd (int — annual gross), "
            "max_usd (int — annual gross), "
            "median_usd (int — annual gross), "
            "currency (str — ISO 4217, default USD), "
            "confidence (str — low | medium | high), "
            "reasoning (str — one concise sentence explaining the estimate), "
            "equity_note (str — brief note on typical equity for this stage/role, or null)."
        )
        skills_str = ", ".join(skills[:12]) if skills else "general"
        exp_str = f"{years_experience} years" if years_experience is not None else "unspecified"
        location_str = (location or "Remote") + (" (remote)" if remote else "")

        user_content = (
            f"Role: {title}\n"
            f"Location: {location_str}\n"
            f"Key skills: {skills_str}\n"
            f"Experience: {exp_str}"
        )
        return await self._chat(system, user_content)
