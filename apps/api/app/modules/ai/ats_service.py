"""
ATS (Applicant Tracking System) scoring service.
Scores a parsed resume against a job description across five dimensions.
No LLM call — fully deterministic, fast, and reproducible.
"""
import re
from typing import TypedDict


class ATSBreakdown(TypedDict):
    keyword_match: float
    skills_overlap: float
    action_verbs: float
    quantified_achievements: float
    section_completeness: float


_ACTION_VERBS = frozenset({
    "implemented", "developed", "designed", "built", "created", "led", "managed",
    "optimized", "improved", "increased", "reduced", "deployed", "architected",
    "launched", "scaled", "automated", "integrated", "delivered", "shipped",
    "mentored", "collaborated", "analyzed", "established", "engineered", "refactored",
    "migrated", "debugged", "released", "documented", "contributed", "accelerated",
    "streamlined", "coordinated", "spearheaded", "drove", "enabled", "achieved",
})

_STOP_WORDS = frozenset({
    "the", "and", "for", "with", "that", "this", "from", "are", "was",
    "will", "have", "been", "not", "but", "our", "you", "your", "its",
    "can", "all", "about", "into", "more", "also", "their", "which",
})


def _extract_words(text: str) -> set[str]:
    return {w for w in re.findall(r"\b[a-z][a-z0-9+#.]{2,}\b", text.lower()) if w not in _STOP_WORDS}


def _flatten_resume(parsed: dict) -> str:
    parts: list[str] = []
    pi = parsed.get("personal_information", {})
    if isinstance(pi, dict):
        parts.append(pi.get("raw_header", ""))
    for exp in parsed.get("experience", []):
        if isinstance(exp, dict):
            parts.append(exp.get("title", ""))
            parts.append(exp.get("company", ""))
            parts.append(exp.get("description", ""))
            parts.extend(exp.get("achievements", []))
    for skill in parsed.get("skills", []):
        parts.append(skill["name"] if isinstance(skill, dict) else skill)
    for edu in parsed.get("education", []):
        if isinstance(edu, dict):
            parts.append(edu.get("institution", ""))
            parts.append(edu.get("degree", "") or "")
    for proj in parsed.get("projects", []):
        if isinstance(proj, dict):
            parts.append(proj.get("name", ""))
            parts.append(proj.get("description", "") or "")
    if parsed.get("summary"):
        parts.append(parsed["summary"])
    return " ".join(str(p) for p in parts if p)


def score_resume(parsed_resume: dict, job_description: str) -> dict:
    """
    Returns a dict with ats_score (0-100), breakdown, missing_keywords, and suggestions.
    """
    experience: list[dict] = [e for e in parsed_resume.get("experience", []) if isinstance(e, dict)]
    skills: list[str] = [
        s["name"] if isinstance(s, dict) else s
        for s in parsed_resume.get("skills", [])
    ]

    resume_text = _flatten_resume(parsed_resume)
    resume_words = _extract_words(resume_text)
    job_words = _extract_words(job_description)

    # 1. Keyword match — up to 40 pts
    overlap = resume_words & job_words
    keyword_score = min((len(overlap) / max(len(job_words), 1)) * 160, 40.0)

    # 2. Skills overlap — up to 20 pts
    skill_names_lower = {s.lower() for s in skills}
    job_skill_hits = sum(1 for w in job_words if w in skill_names_lower)
    skills_score = min((job_skill_hits / max(len(job_words) * 0.05, 1)) * 20, 20.0)

    # 3. Action verbs — up to 15 pts
    all_bullets = [ach for exp in experience for ach in exp.get("achievements", []) if ach]
    verb_count = sum(
        1 for b in all_bullets
        if any(b.lower().startswith(v) or f" {v} " in b.lower() for v in _ACTION_VERBS)
    )
    action_score = min((verb_count / max(len(all_bullets), 1)) * 15, 15.0) if all_bullets else 0.0

    # 4. Quantified achievements — up to 15 pts
    quantified = sum(1 for b in all_bullets if re.search(r"\b\d+[%x]?\b", b))
    quant_score = min((quantified / max(len(all_bullets), 1)) * 15, 15.0) if all_bullets else 0.0

    # 5. Section completeness — up to 10 pts
    sections = {
        "summary": bool(parsed_resume.get("personal_information") or parsed_resume.get("summary")),
        "experience": bool(experience),
        "skills": bool(skills),
        "education": bool(parsed_resume.get("education")),
    }
    completeness_score = sum(2.5 for v in sections.values() if v)

    total = round(keyword_score + skills_score + action_score + quant_score + completeness_score, 1)

    # Missing keywords (meaningful ones from job not in resume)
    missing_kw = sorted(job_words - resume_words - _STOP_WORDS)[:25]

    suggestions: list[str] = []
    if not sections["summary"]:
        suggestions.append("Add a professional summary to improve ATS compatibility.")
    if action_score < 8:
        suggestions.append("Start more bullet points with strong action verbs (Implemented, Deployed, Led…).")
    if quant_score < 8:
        suggestions.append("Quantify achievements with numbers, percentages, or scale metrics.")
    if keyword_score < 20:
        suggestions.append("Incorporate more keywords from the job description into your resume.")
    if not sections["skills"]:
        suggestions.append("Add a dedicated Skills section.")

    return {
        "ats_score": total,
        "breakdown": ATSBreakdown(
            keyword_match=round(keyword_score, 1),
            skills_overlap=round(skills_score, 1),
            action_verbs=round(action_score, 1),
            quantified_achievements=round(quant_score, 1),
            section_completeness=round(completeness_score, 1),
        ),
        "sections_present": sections,
        "missing_keywords": missing_kw,
        "suggestions": suggestions,
    }
