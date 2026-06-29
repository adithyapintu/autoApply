# Database Package

The canonical SQLAlchemy models and Alembic migrations live in `apps/api/app/db` and `apps/api/alembic`.

## Normalized Tables

- users
- profiles
- skills
- experience
- education
- projects
- resumes
- resume_versions
- companies
- jobs
- applications
- automation_tasks
- notifications
- email_events
- audit_logs
- system_settings

## Indexing Plan

- Unique index on users.email.
- Unique index on jobs.source and jobs.external_id.
- Compound index on skills.profile_id and skills.name.
- Add pgvector indexes for profile and job embeddings when embedding columns are introduced.

