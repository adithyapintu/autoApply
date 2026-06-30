import asyncio

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "autoapply",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.task_routes = {
    "app.worker.parse_resume": {"queue": "parsing"},
    "app.worker.discover_jobs": {"queue": "discovery"},
    "app.worker.match_jobs": {"queue": "ai"},
    "app.worker.embed_job": {"queue": "ai"},
    "app.worker.embed_profile": {"queue": "ai"},
    "app.worker.run_automation": {"queue": "automation"},
    "app.worker.submit_application": {"queue": "automation"},
    "app.worker.process_saved_search": {"queue": "discovery"},
    "app.worker.process_all_saved_searches": {"queue": "discovery"},
    "app.worker.sync_email": {"queue": "email"},
    "app.worker.send_notification": {"queue": "notifications"},
}

celery_app.conf.beat_schedule = {
    "process-saved-searches-daily": {
        "task": "app.worker.process_all_saved_searches",
        "schedule": 3600 * 6,  # every 6 hours
    },
}


def _run(coro):
    """Run an async coroutine from a sync Celery task."""
    return asyncio.run(coro)


@celery_app.task(name="app.worker.parse_resume", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def parse_resume(resume_id: str) -> dict[str, str]:
    async def _inner():
        from app.db.session import get_session
        from app.db.repositories import UnitOfWork
        from app.modules.resumes.parser import ResumeParser
        import tempfile, httpx
        from pathlib import Path

        async for session in get_session():
            uow = UnitOfWork(session)
            resume = await uow.resumes.get(__import__("uuid").UUID(resume_id))
            if resume is None:
                return {"error": "resume_not_found"}

            parser = ResumeParser()
            # For now parse from stored text if parsed_json has raw content, else skip
            if resume.parsed_json and resume.parsed_json.get("raw_text"):
                raw_text = resume.parsed_json["raw_text"]
                parsed = await parser.parse_with_ai(raw_text)
                data = parsed.model_dump()
                data["ai_parsed"] = True
                await uow.resumes.update_parsed(resume.id, data)
                await uow.commit()
            return {"resume_id": resume_id, "status": "parsed"}

    return _run(_inner())


@celery_app.task(name="app.worker.discover_jobs", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def discover_jobs(user_id: str, source: str, query: str = "", location: str | None = None) -> dict:
    async def _inner():
        from app.modules.jobs.connectors.registry import get_connector, get_keyword_connectors
        from app.db.session import get_session
        from app.db.repositories import UnitOfWork
        import asyncio

        # source="all" fans out across all keyword-based connectors in parallel
        if source == "all":
            connectors = get_keyword_connectors()
            dto_lists = await asyncio.gather(
                *[c.search(query=query, location=location, limit=25) for c in connectors],
                return_exceptions=True,
            )
            dtos = [dto for result in dto_lists if isinstance(result, list) for dto in result]
        else:
            connector = get_connector(source)
            if connector is None:
                return {"error": f"unknown_source:{source}"}
            dtos = await connector.search(query=query, location=location, limit=50)

        async for session in get_session():
            uow = UnitOfWork(session)
            job_ids = []
            for dto in dtos:
                job = await uow.jobs.upsert_from_dto(dto.model_dump(mode="json"))
                job_ids.append(str(job.id))
            await uow.commit()

        for job_id in job_ids:
            embed_job.delay(job_id)

        return {"user_id": user_id, "source": source, "jobs_saved": len(job_ids)}

    return _run(_inner())


@celery_app.task(name="app.worker.match_jobs", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def match_jobs(user_id: str) -> dict:
    async def _inner():
        from app.db.session import get_session
        from app.db.repositories import UnitOfWork
        from app.modules.jobs.matcher import JobMatcher
        import uuid

        async for session in get_session():
            uow = UnitOfWork(session)
            profile = await uow.profiles.find_by_user(uuid.UUID(user_id))
            if profile is None:
                return {"error": "profile_not_found"}

            profile_dict = {
                "skills": [s.name for s in profile.skills],
                "tech_stacks": profile.tech_stacks,
                "field": profile.field,
                "seniority": profile.seniority,
            }
            jobs = await uow.jobs.search(None, limit=200)
            matcher = JobMatcher()
            scored = 0
            for job in jobs:
                job_dict = {"required_skills": list(profile.tech_stacks)}
                report = matcher.score(profile_dict, job_dict)
                # Store match score on new applications created for this user
                scored += 1
            return {"user_id": user_id, "jobs_scored": scored}

    return _run(_inner())


@celery_app.task(name="app.worker.sync_email", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def sync_email(user_id: str) -> dict[str, str]:
    # Email OAuth integration (Gmail/Outlook) — Phase 1.3 auth flows required first
    return {"user_id": user_id, "status": "email_sync_requires_oauth_setup"}


@celery_app.task(name="app.worker.send_notification", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_notification(notification_id: str) -> dict[str, str]:
    async def _inner():
        from app.db.session import get_session
        from app.db.repositories import UnitOfWork
        import uuid, smtplib
        from email.message import EmailMessage

        async for session in get_session():
            uow = UnitOfWork(session)
            notif = await session.get(
                __import__("app.db.models", fromlist=["Notification"]).Notification,
                uuid.UUID(notification_id),
            )
            if notif is None:
                return {"error": "notification_not_found"}

            if notif.channel == "email" and settings.smtp_host:
                msg = EmailMessage()
                msg["Subject"] = notif.subject
                msg["From"] = settings.email_from
                user = await uow.users.find_by_id(notif.user_id)
                msg["To"] = user.email if user else ""
                msg.set_content(notif.body)
                try:
                    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
                        if settings.smtp_username:
                            smtp.login(settings.smtp_username, settings.smtp_password or "")
                        smtp.send_message(msg)
                    notif.status = "delivered"
                except Exception as exc:
                    notif.status = f"failed:{exc}"
            else:
                notif.status = "skipped_no_channel"

            await uow.commit()
            return {"notification_id": notification_id, "status": notif.status}

    return _run(_inner())


@celery_app.task(name="app.worker.embed_job", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def embed_job(job_id: str) -> dict:
    async def _inner():
        from app.db.session import get_session
        from app.db.repositories import UnitOfWork
        from app.modules.ai.embedding_service import EmbeddingService
        import uuid

        svc = EmbeddingService()
        async for session in get_session():
            uow = UnitOfWork(session)
            job = await uow.jobs.get(uuid.UUID(job_id))
            if job is None:
                return {"error": "job_not_found"}
            text = svc.build_job_text({"title": job.title, "description": job.description, "location": job.location})
            embedding = await svc.embed(text)
            await uow.jobs.update_embedding(job.id, embedding)
            await uow.commit()
            return {"job_id": job_id, "status": "embedded", "dim": len(embedding)}

    return _run(_inner())


@celery_app.task(name="app.worker.embed_profile", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def embed_profile(user_id: str) -> dict:
    async def _inner():
        from app.db.session import get_session
        from app.db.repositories import UnitOfWork
        from app.modules.ai.embedding_service import EmbeddingService
        import uuid

        svc = EmbeddingService()
        async for session in get_session():
            uow = UnitOfWork(session)
            profile = await uow.profiles.find_by_user(uuid.UUID(user_id))
            if profile is None:
                return {"error": "profile_not_found"}
            profile_dict = {
                "field": profile.field,
                "tech_stacks": profile.tech_stacks,
                "preferred_roles": profile.preferred_roles,
                "summary": profile.summary,
                "skills": [{"name": s.name} for s in profile.skills],
                "experience": [
                    {"title": e.title, "company": e.company, "achievements": e.achievements}
                    for e in profile.experience
                ],
            }
            text = svc.build_profile_text(profile_dict)
            embedding = await svc.embed(text)
            await uow.profiles.update_embedding(profile.id, embedding)
            await uow.commit()
            return {"user_id": user_id, "status": "embedded", "dim": len(embedding)}

    return _run(_inner())


# ── Phase 3: Auto-Apply ───────────────────────────────────────────────────────

@celery_app.task(name="app.worker.run_automation", autoretry_for=(Exception,), retry_backoff=True, max_retries=2)
def run_automation(task_id: str, target_url: str, site_adapter: str, answers: dict) -> dict:
    async def _inner():
        from app.db.session import get_session
        from app.db.repositories import UnitOfWork
        from app.db import models
        from app.modules.automation.engine import BrowserAutomationEngine
        from app.modules.automation.engine import AutomationTask as EngineTask
        import uuid

        async for session in get_session():
            uow = UnitOfWork(session)
            db_task = await session.get(models.AutomationTask, uuid.UUID(task_id))
            if db_task is None:
                return {"error": "task_not_found"}

            db_task.status = "running"
            await uow.commit()

            engine_task = EngineTask(
                application_id=task_id,
                target_url=target_url,
                site_adapter=site_adapter,
                answers=answers,
            )
            try:
                engine = BrowserAutomationEngine()
                checkpoint = await engine.prepare_until_approval(engine_task)
                db_task = await session.get(models.AutomationTask, uuid.UUID(task_id))
                db_task.status = "awaiting_approval"
                db_task.checkpoint = {
                    "summary": checkpoint.summary,
                    "submit_selector": checkpoint.submit_selector,
                    "screenshot_path": checkpoint.screenshot_path,
                }
                if checkpoint.screenshot_path:
                    db_task.screenshots = [checkpoint.screenshot_path]
                await uow.commit()
                return {"task_id": task_id, "status": "awaiting_approval"}
            except Exception as exc:
                db_task = await session.get(models.AutomationTask, uuid.UUID(task_id))
                db_task.status = "failed"
                db_task.error = str(exc)
                await uow.commit()
                raise

    return _run(_inner())


@celery_app.task(name="app.worker.submit_application", autoretry_for=(Exception,), retry_backoff=True, max_retries=2)
def submit_application(task_id: str) -> dict:
    async def _inner():
        from app.db.session import get_session
        from app.db.repositories import UnitOfWork
        from app.db import models
        from app.modules.automation.engine import BrowserAutomationEngine, ApprovalCheckpoint
        from app.modules.automation.engine import AutomationTask as EngineTask
        import uuid

        async for session in get_session():
            uow = UnitOfWork(session)
            db_task = await session.get(models.AutomationTask, uuid.UUID(task_id))
            if db_task is None or db_task.status != "approved":
                return {"error": "task_not_approved"}

            checkpoint_data = db_task.checkpoint or {}
            checkpoint = ApprovalCheckpoint(
                summary=checkpoint_data.get("summary", {}),
                screenshot_path=checkpoint_data.get("screenshot_path"),
                submit_selector=checkpoint_data.get("submit_selector", "button[type=submit]"),
            )

            app_record = await uow.applications.get(db_task.application_id)
            job = await uow.jobs.get(app_record.job_id) if app_record else None
            if not job:
                return {"error": "job_not_found"}

            engine_task = EngineTask(
                application_id=task_id,
                target_url=job.url,
                site_adapter=db_task.site_adapter,
            )
            try:
                engine = BrowserAutomationEngine()
                await engine.submit_after_approval(engine_task, checkpoint)
                db_task.status = "submitted"
                if app_record:
                    app_record.status = "applied"
                    from datetime import UTC, datetime
                    app_record.applied_at = datetime.now(UTC)
                await uow.commit()
                return {"task_id": task_id, "status": "submitted"}
            except Exception as exc:
                db_task.status = "failed"
                db_task.error = str(exc)
                await uow.commit()
                raise

    return _run(_inner())


# ── Phase 3: Saved Searches ───────────────────────────────────────────────────

@celery_app.task(name="app.worker.process_saved_search", autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def process_saved_search(search_id: str, user_id: str) -> dict:
    async def _inner():
        from app.db.session import get_session
        from app.db.repositories import UnitOfWork
        from app.db import models
        from app.modules.jobs.connectors.registry import get_connector
        from app.modules.jobs.matcher import JobMatcher
        import uuid

        async for session in get_session():
            uow = UnitOfWork(session)
            ss = await uow.saved_searches.get(uuid.UUID(search_id))
            if ss is None or not ss.is_active:
                return {"error": "search_not_found"}

            connector = get_connector(ss.source)
            if connector is None:
                return {"error": f"unknown_source:{ss.source}"}

            dtos = await connector.search(query=ss.query, location=ss.location, limit=50)
            new_jobs = []
            for dto in dtos:
                job = await uow.jobs.upsert_from_dto(dto.model_dump(mode="json"))
                new_jobs.append(job)
            await uow.commit()

            # Score new jobs against user profile
            profile = await uow.profiles.find_by_user(uuid.UUID(user_id))
            if profile:
                matcher = JobMatcher()
                profile_dict = {
                    "skills": [s.name for s in profile.skills],
                    "tech_stacks": profile.tech_stacks,
                }
                threshold = float(ss.score_threshold)
                high_matches = []
                for job in new_jobs:
                    report = matcher.score(profile_dict, {"required_skills": []},
                                          list(profile.embedding) if profile.embedding else None,
                                          list(job.embedding) if job.embedding else None)
                    if report.overall_score >= threshold:
                        high_matches.append({"title": job.title, "score": report.overall_score})

                # Notify user about high-match jobs
                if high_matches:
                    body = "\n".join(f"• {m['title']} (score: {m['score']:.0f})" for m in high_matches[:10])
                    notif = models.Notification(
                        user_id=uuid.UUID(user_id),
                        channel="email",
                        subject=f"🎯 {len(high_matches)} new job match(es) for '{ss.name}'",
                        body=f"New jobs matching your saved search '{ss.name}':\n\n{body}",
                        status="pending",
                    )
                    session.add(notif)

            await uow.saved_searches.mark_ran(uuid.UUID(search_id))
            await uow.commit()

            # Queue embeddings for new jobs
            for job in new_jobs:
                embed_job.delay(str(job.id))

            return {"search_id": search_id, "new_jobs": len(new_jobs)}

    return _run(_inner())


@celery_app.task(name="app.worker.process_all_saved_searches")
def process_all_saved_searches() -> dict:
    async def _inner():
        from app.db.session import get_session
        from app.db.repositories import UnitOfWork

        async for session in get_session():
            uow = UnitOfWork(session)
            due_searches = await uow.saved_searches.list_due()
            for ss in due_searches:
                process_saved_search.delay(str(ss.id), str(ss.user_id))
            return {"searches_queued": len(due_searches)}

    return _run(_inner())

