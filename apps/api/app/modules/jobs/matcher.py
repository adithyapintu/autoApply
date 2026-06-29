from app.modules.jobs.schemas import MatchReport


class JobMatcher:
    def score(self, profile: dict, job: dict) -> MatchReport:
        profile_skills = {skill.lower() for skill in profile.get("skills", [])}
        job_skills = {skill.lower() for skill in job.get("required_skills", [])}
        matched = sorted(profile_skills & job_skills)
        missing = sorted(job_skills - profile_skills)
        skill_score = 100.0 if not job_skills else (len(matched) / len(job_skills)) * 100
        return MatchReport(
            overall_score=round(skill_score, 2),
            reasons=[f"Matched {len(matched)} of {len(job_skills)} required skills"],
            missing_skills=missing,
            strengths=matched,
            recommendation="apply" if skill_score >= 75 else "review" if skill_score >= 50 else "skip",
        )

