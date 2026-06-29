from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


class ApplicationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: UUID, job_id: UUID) -> models.Application:
        application = models.Application(user_id=user_id, job_id=job_id, status="draft")
        self.session.add(application)
        await self.session.flush()
        return application

    async def list_for_user(self, user_id: UUID) -> list[models.Application]:
        result = await self.session.execute(
            select(models.Application)
            .where(models.Application.user_id == user_id)
            .order_by(models.Application.created_at.desc())
        )
        return list(result.scalars().all())


class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.jobs = JobRepository(session)
        self.applications = ApplicationRepository(session)

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

