from app.modules.jobs.matcher import JobMatcher


def test_matcher_reports_strengths_and_missing_skills() -> None:
    report = JobMatcher().score(
        profile={"skills": ["Python", "FastAPI", "Redis"]},
        job={"required_skills": ["Python", "Kubernetes"]},
    )

    assert report.overall_score == 50
    assert report.strengths == ["python"]
    assert report.missing_skills == ["kubernetes"]
    assert report.recommendation == "review"

