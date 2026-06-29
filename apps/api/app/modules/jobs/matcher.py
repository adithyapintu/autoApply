import math

from app.modules.jobs.schemas import MatchReport


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class JobMatcher:
    def score(
        self,
        profile: dict,
        job: dict,
        profile_embedding: list[float] | None = None,
        job_embedding: list[float] | None = None,
    ) -> MatchReport:
        profile_skills = {skill.lower() for skill in profile.get("skills", [])}
        job_skills = {skill.lower() for skill in job.get("required_skills", [])}

        # Also pull tech_stacks into the profile skill set
        profile_skills |= {s.lower() for s in profile.get("tech_stacks", [])}

        matched = sorted(profile_skills & job_skills)
        missing = sorted(job_skills - profile_skills)
        skill_score = 100.0 if not job_skills else (len(matched) / len(job_skills)) * 100

        reasons = [f"Matched {len(matched)} of {len(job_skills)} required skills"]

        if profile_embedding and job_embedding:
            vector_score = _cosine_similarity(profile_embedding, job_embedding) * 100
            overall_score = 0.6 * vector_score + 0.4 * skill_score
            reasons.append(f"Semantic similarity: {vector_score:.0f}/100")
        else:
            overall_score = skill_score

        recommendation = "apply" if overall_score >= 75 else "review" if overall_score >= 50 else "skip"

        return MatchReport(
            overall_score=round(overall_score, 2),
            reasons=reasons,
            missing_skills=missing,
            strengths=matched,
            recommendation=recommendation,
        )

