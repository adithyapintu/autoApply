# AutoApply AI

Production-oriented SaaS scaffold for AI-assisted job discovery, matching, application material generation, browser-assisted form filling, and application tracking.

AutoApply AI is designed around one non-negotiable safety rule: automation may prepare and fill an application, but it must pause before final submission and require explicit user approval.

## Monorepo Layout

```text
apps/
  api/        FastAPI service, REST API, SQLAlchemy, Alembic
  web/        Next.js dashboard
  worker/     Celery workers for parsing, matching, email sync, notifications
packages/
  ai/         Prompt templates and AI service contracts
  database/   Database documentation and migration notes
  playwright/ Browser automation adapter contracts
  shared/     TypeScript DTOs shared with the frontend
  ui/         Shared UI primitives
config/       Nginx and environment config
docs/         Architecture, API, security, deployment, prompt docs
infra/        Kubernetes and Terraform starter config
scripts/      Developer helper scripts
```

## Quick Start

1. Copy `.env.example` to `.env`.
2. Fill secrets and OAuth credentials.
3. Run `docker compose up --build`.
4. Open the API docs at `http://localhost:8000/docs`.
5. Open the web app at `http://localhost:3000`.

## What Is Implemented

- FastAPI application with versioned REST routes.
- JWT auth scaffolding with refresh tokens, email verification, password reset, and Google OAuth entry points.
- Normalized SQLAlchemy data model and Alembic migration for users, profiles, skills, resumes, jobs, applications, notifications, email events, audit logs, and settings.
- Pluggable job connector architecture for Greenhouse, Lever, Ashby, SmartRecruiters, Workday, Wellfound, and permitted company pages.
- AI service contracts for parsing, matching, resume optimization, cover letters, Q&A, company summaries, salary estimation, and interview preparation.
- Playwright automation architecture that stops at a user approval gate before submission.
- Celery worker tasks for resume parsing, job discovery, matching, email sync, and notification delivery.
- Next.js dashboard skeleton with typed API client and application analytics views.
- Docker Compose, Kubernetes manifests, GitHub Actions CI, and Terraform starter files.
- Documentation for architecture, API design, security, deployment, prompts, and contribution.

## Safety Constraints

- Never fabricate candidate qualifications or application content.
- Prefer official APIs and documented integrations over UI automation.
- Do not bypass CAPTCHAs, authentication protections, anti-bot systems, or website terms.
- Require explicit user approval before final application submission.
- Log automation actions and store screenshots for auditable recovery.

