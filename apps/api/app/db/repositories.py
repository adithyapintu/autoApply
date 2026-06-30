from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import models


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_email(self, email: str) -> models.User | None:
        result = await self.session.execute(select(models.User).where(models.User.email == email.lower()))
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: UUID) -> models.User | None:
        return await self.session.get(models.User, user_id)

    async def create(self, email: str, password_hash: str | None, full_name: str | None) -> models.User:
        user = models.User(email=email.lower(), password_hash=password_hash, full_name=full_name)
        self.session.add(user)
        await self.session.flush()
        return user

    async def update_verified(self, user_id: UUID) -> None:
        user = await self.session.get(models.User, user_id)
        if user:
            user.is_email_verified = True
            await self.session.flush()

    async def update_password(self, user_id: UUID, password_hash: str) -> None:
        user = await self.session.get(models.User, user_id)
        if user:
            user.password_hash = password_hash
            await self.session.flush()


class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_user(self, user_id: UUID) -> models.Profile | None:
        result = await self.session.execute(
            select(models.Profile)
            .where(models.Profile.user_id == user_id)
            .options(
                selectinload(models.Profile.skills),
                selectinload(models.Profile.experience),
                selectinload(models.Profile.education),
                selectinload(models.Profile.projects),
            )
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: UUID, data: dict) -> models.Profile:
        from sqlalchemy import delete as sa_delete

        profile = await self.find_by_user(user_id)
        skills_data = data.pop("skills", None)
        experience_data = data.pop("experience", None)
        education_data = data.pop("education", None)
        projects_data = data.pop("projects", None)

        if profile is None:
            profile = models.Profile(user_id=user_id, **data)
            self.session.add(profile)
        else:
            for key, value in data.items():
                setattr(profile, key, value)
        await self.session.flush()

        if skills_data is not None:
            await self.session.execute(
                sa_delete(models.Skill).where(models.Skill.profile_id == profile.id)
            )
            for s in skills_data:
                self.session.add(models.Skill(profile_id=profile.id, **s))

        if experience_data is not None:
            await self.session.execute(
                sa_delete(models.Experience).where(models.Experience.profile_id == profile.id)
            )
            for e in experience_data:
                self.session.add(models.Experience(profile_id=profile.id, **e))

        if education_data is not None:
            await self.session.execute(
                sa_delete(models.Education).where(models.Education.profile_id == profile.id)
            )
            for edu in education_data:
                self.session.add(models.Education(profile_id=profile.id, **edu))

        if projects_data is not None:
            await self.session.execute(
                sa_delete(models.Project).where(models.Project.profile_id == profile.id)
            )
            for p in projects_data:
                self.session.add(models.Project(profile_id=profile.id, **p))

        await self.session.flush()
        return profile


    async def update_embedding(self, profile_id: UUID, embedding: list[float]) -> None:
        profile = await self.session.get(models.Profile, profile_id)
        if profile:
            profile.embedding = embedding
            await self.session.flush()


class ResumeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        file_name: str,
        mime_type: str,
        storage_key: str,
        sha256: str,
        parsed_json: dict | None = None,
    ) -> models.Resume:
        resume = models.Resume(
            user_id=user_id,
            file_name=file_name,
            mime_type=mime_type,
            storage_key=storage_key,
            sha256=sha256,
            parsed_json=parsed_json,
        )
        self.session.add(resume)
        await self.session.flush()
        return resume

    async def get(self, resume_id: UUID) -> models.Resume | None:
        return await self.session.get(models.Resume, resume_id)

    async def list_for_user(self, user_id: UUID) -> list[models.Resume]:
        result = await self.session.execute(
            select(models.Resume)
            .where(models.Resume.user_id == user_id)
            .order_by(models.Resume.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_parsed(self, resume_id: UUID, parsed_json: dict) -> None:
        resume = await self.session.get(models.Resume, resume_id)
        if resume:
            resume.parsed_json = parsed_json
            await self.session.flush()

    async def delete(self, resume_id: UUID) -> None:
        resume = await self.session.get(models.Resume, resume_id)
        if resume:
            await self.session.delete(resume)
            await self.session.flush()


class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(self, query: str | None, limit: int = 25) -> list[models.Job]:
        stmt = select(models.Job).limit(limit).order_by(models.Job.created_at.desc())
        if query:
            like = f"%{query}%"
            stmt = stmt.where(models.Job.title.ilike(like) | models.Job.description.ilike(like))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, job_id: UUID) -> models.Job | None:
        return await self.session.get(models.Job, job_id)

    async def update_embedding(self, job_id: UUID, embedding: list[float]) -> None:
        job = await self.session.get(models.Job, job_id)
        if job:
            job.embedding = embedding
            await self.session.flush()

    async def search_by_vector(self, embedding: list[float], limit: int = 25) -> list[models.Job]:
        """Cosine-similarity nearest-neighbour search via pgvector."""
        from pgvector.sqlalchemy import cosine_distance
        result = await self.session.execute(
            select(models.Job)
            .where(models.Job.embedding.isnot(None))
            .order_by(cosine_distance(models.Job.embedding, embedding))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_descriptions(self, limit: int = 500) -> list[str]:
        result = await self.session.execute(
            select(models.Job.description).limit(limit)
        )
        return [row[0] for row in result.all() if row[0]]

    async def upsert_from_dto(self, dto: dict) -> models.Job:
        result = await self.session.execute(
            select(models.Job).where(
                models.Job.source == dto["source"],
                models.Job.external_id == dto["external_id"],
            )
        )
        job = result.scalar_one_or_none()
        if job is None:
            company = await self._get_or_create_company(dto.get("company", "Unknown"))
            job = models.Job(
                company_id=company.id,
                source=dto["source"],
                external_id=dto["external_id"],
                title=dto["title"],
                description=dto.get("description", ""),
                location=dto.get("location"),
                remote_policy=dto.get("remote_policy"),
                employment_type=dto.get("employment_type"),
                salary_min=dto.get("salary_min"),
                salary_max=dto.get("salary_max"),
                visa_sponsorship=dto.get("visa_sponsorship"),
                url=str(dto["url"]),
                raw_payload=dto,
            )
            self.session.add(job)
            await self.session.flush()
        return job

    async def _get_or_create_company(self, name: str) -> models.Company:
        result = await self.session.execute(
            select(models.Company).where(models.Company.name == name)
        )
        company = result.scalar_one_or_none()
        if company is None:
            company = models.Company(name=name)
            self.session.add(company)
            await self.session.flush()
        return company


class ApplicationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        job_id: UUID,
        referred_by: str | None = None,
        referral_channel: str | None = None,
    ) -> models.Application:
        application = models.Application(
            user_id=user_id, job_id=job_id, status="draft",
            referred_by=referred_by, referral_channel=referral_channel,
        )
        self.session.add(application)
        await self.session.flush()
        return application

    async def get(self, application_id: UUID) -> models.Application | None:
        return await self.session.get(models.Application, application_id)

    async def list_for_user(self, user_id: UUID) -> list[models.Application]:
        result = await self.session.execute(
            select(models.Application)
            .where(models.Application.user_id == user_id)
            .order_by(models.Application.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_with_jobs(self, user_id: UUID) -> list[tuple[models.Application, models.Job | None]]:
        result = await self.session.execute(
            select(models.Application, models.Job)
            .outerjoin(models.Job, models.Application.job_id == models.Job.id)
            .where(models.Application.user_id == user_id)
            .order_by(models.Application.created_at.desc())
        )
        return [(row[0], row[1]) for row in result.all()]

    async def update_status(self, application_id: UUID, status: str) -> None:
        app = await self.session.get(models.Application, application_id)
        if app:
            app.status = status
            await self.session.flush()

    async def counts_for_user(self, user_id: UUID) -> dict:
        apps = await self.list_for_user(user_id)
        from collections import Counter
        counts = Counter(a.status for a in apps)
        return dict(counts)


class SavedSearchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_user(self, user_id: UUID) -> list[models.SavedSearch]:
        result = await self.session.execute(
            select(models.SavedSearch)
            .where(models.SavedSearch.user_id == user_id)
            .order_by(models.SavedSearch.created_at.desc())
        )
        return list(result.scalars().all())

    async def create(self, user_id: UUID, data: dict) -> models.SavedSearch:
        ss = models.SavedSearch(user_id=user_id, **data)
        self.session.add(ss)
        await self.session.flush()
        return ss

    async def get(self, search_id: UUID) -> models.SavedSearch | None:
        return await self.session.get(models.SavedSearch, search_id)

    async def delete(self, search_id: UUID) -> None:
        ss = await self.session.get(models.SavedSearch, search_id)
        if ss:
            await self.session.delete(ss)

    async def list_due(self) -> list[models.SavedSearch]:
        """Return active searches whose last_run_at is overdue."""
        from datetime import UTC, datetime, timedelta
        from sqlalchemy import or_
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(models.SavedSearch)
            .where(models.SavedSearch.is_active.is_(True))
            .where(
                or_(
                    models.SavedSearch.last_run_at.is_(None),
                    models.SavedSearch.last_run_at
                    <= now - timedelta(hours=1) * models.SavedSearch.interval_hours,
                )
            )
        )
        return list(result.scalars().all())

    async def mark_ran(self, search_id: UUID) -> None:
        from datetime import UTC, datetime
        ss = await self.session.get(models.SavedSearch, search_id)
        if ss:
            ss.last_run_at = datetime.now(UTC)
            await self.session.flush()


class TaskLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: UUID, celery_task_id: str, task_name: str, params: dict) -> models.TaskLog:
        log = models.TaskLog(
            user_id=user_id,
            celery_task_id=celery_task_id,
            task_name=task_name,
            status="pending",
            params=params,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def list_for_user(self, user_id: UUID, limit: int = 50) -> list[models.TaskLog]:
        result = await self.session.execute(
            select(models.TaskLog)
            .where(models.TaskLog.user_id == user_id)
            .order_by(models.TaskLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_celery_id(self, celery_task_id: str) -> models.TaskLog | None:
        result = await self.session.execute(
            select(models.TaskLog).where(models.TaskLog.celery_task_id == celery_task_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, celery_task_id: str, status: str, result: dict | None = None, error: str | None = None) -> None:
        log = await self.get_by_celery_id(celery_task_id)
        if log:
            log.status = status
            if result is not None:
                log.result = result
            if error is not None:
                log.error = error
            await self.session.flush()


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.profiles = ProfileRepository(session)
        self.resumes = ResumeRepository(session)
        self.jobs = JobRepository(session)
        self.applications = ApplicationRepository(session)
        self.saved_searches = SavedSearchRepository(session)
        self.task_logs = TaskLogRepository(session)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

