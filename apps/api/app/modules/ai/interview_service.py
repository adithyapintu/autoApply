"""
Interview preparation service.
Generates behavioural Q&A (STAR), technical questions, and talking points.
Answers are grounded strictly in the candidate's real profile — no fabrication.
"""
import json

from app.modules.ai.services import BaseAIService


class InterviewPrepService(BaseAIService):
    async def generate(self, profile: dict, job: dict) -> dict:
        system = (
            "You are an expert interview coach. "
            "Generate a targeted interview prep guide for the candidate. "
            "IMPORTANT: Answers and talking points must be traceable to the candidate's actual "
            "experience, projects, or achievements. Never fabricate examples. "
            "If the profile lacks enough context for a suggested answer, set suggested_answer to null "
            "and note what the candidate should fill in. "
            "Return JSON with keys:\n"
            "  behavioral_questions: list of {question, theme, suggested_answer (str|null), star_hints (list[str])}\n"
            "  technical_questions: list of {question, topic, difficulty (easy|medium|hard), why_relevant}\n"
            "  company_questions: list of str (questions to ask the interviewer)\n"
            "  talking_points: list of str (3-5 key strengths to highlight for this specific role)\n"
            "  preparation_tips: list of str (2-3 role-specific preparation suggestions)\n"
            "Aim for 4-6 behavioral, 5-8 technical, 3 company questions."
        )
        profile_summary = {
            "field": profile.get("field"),
            "tech_stacks": profile.get("tech_stacks", []),
            "skills": [s["name"] if isinstance(s, dict) else s for s in profile.get("skills", [])][:20],
            "summary": profile.get("summary"),
            "experience": [
                {
                    "title": e.get("title") if isinstance(e, dict) else "",
                    "company": e.get("company") if isinstance(e, dict) else "",
                    "achievements": (e.get("achievements", []) if isinstance(e, dict) else [])[:3],
                }
                for e in profile.get("experience", [])[:4]
            ],
            "projects": [
                {
                    "name": p.get("name") if isinstance(p, dict) else "",
                    "skills": (p.get("skills", []) if isinstance(p, dict) else [])[:5],
                }
                for p in profile.get("projects", [])[:3]
            ],
        }
        job_summary = {
            "title": job.get("title", ""),
            "description": (job.get("description", "") or "")[:2500],
        }
        user_content = (
            f"Candidate profile:\n{json.dumps(profile_summary, indent=2)}\n\n"
            f"Job:\n{json.dumps(job_summary, indent=2)}"
        )
        return await self._chat(system, user_content)
