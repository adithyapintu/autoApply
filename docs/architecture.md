# Architecture

AutoApply AI uses a modular monorepo with independently deployable API, worker, and web applications.

```mermaid
flowchart LR
  Web["Next.js Web App"] --> API["FastAPI REST API"]
  API --> Postgres["PostgreSQL + pgvector"]
  API --> Redis["Redis Cache / Rate Limits"]
  API --> S3["Encrypted Object Storage"]
  API --> Queue["Celery Queue"]
  Worker["Celery Workers"] --> Queue
  Worker --> Postgres
  Worker --> AI["AI Services"]
  Worker --> Email["Gmail / Outlook APIs"]
  API --> Automation["Playwright Automation Engine"]
  Automation --> Approval["User Approval Gate"]
```

## Design Decisions

- **Clean architecture:** API routers are thin; services own business rules; repositories own persistence; unit-of-work controls transactions.
- **Pluggable connectors:** job sources implement a common `JobConnector` contract so new providers do not require core matching changes.
- **Async backend:** FastAPI and SQLAlchemy async support high concurrency for IO-heavy SaaS traffic.
- **Queue-first heavy work:** parsing, embeddings, job discovery, matching, email sync, notification delivery, and automation runs move to workers.
- **Safety by construction:** the automation engine has a mandatory approval checkpoint before any submit action.
- **Provider boundaries:** AI prompts live in independent services and must use candidate-provided facts only.

## Scale Model

- API services scale horizontally behind Nginx or an application load balancer.
- Workers scale by queue type: parsing, AI generation, job discovery, email sync, automation.
- PostgreSQL stores transactional data; pgvector stores embeddings for jobs and profiles.
- Redis handles rate limits, cache-aside reads, short-lived idempotency keys, and Celery transport.
- Object storage holds encrypted resumes, generated versions, screenshots, and audit artifacts.

## Automation Sequence

```mermaid
sequenceDiagram
  participant U as User
  participant API as API
  participant W as Worker
  participant P as Playwright
  participant Site as Job Site

  U->>API: Start application automation
  API->>W: Queue automation task
  W->>P: Launch managed browser
  P->>Site: Login/fill permitted form fields
  P->>W: Extract final summary and screenshot
  W->>API: Store pending approval checkpoint
  API->>U: Show summary, files, answers, screenshot
  U->>API: Confirm submission
  API->>W: Resume task with approval token
  W->>P: Click final submit
  W->>API: Record result and audit log
```

