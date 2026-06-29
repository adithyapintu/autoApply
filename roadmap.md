# AutoApply AI — Product Roadmap

Generated from an architectural review of the codebase as of June 2026.

---

## Architecture Summary

AutoApply AI is a pnpm monorepo with three independently deployable apps (`api`, `web`, `worker`) and five shared packages (`ai`, `database`, `playwright`, `shared`, `ui`).

| Layer | Stack | Current State |
|---|---|---|
| API | FastAPI + SQLAlchemy + Alembic | ✅ Auth, profiles, resumes, jobs, AI, vector search, automation, saved searches, export |
| Web | Next.js 15 + Tailwind | ✅ 10 pages: Dashboard, Jobs, Job Detail, Applications, Automation, Saved Searches, Interview Prep, Resumes, Profile, Settings |
| Worker | Celery + Redis + Beat | ✅ 10 tasks: parse, discover, match, embed×2, run_automation, submit_application, process_saved_search×2, notify |
| AI (text) | Groq `llama-3.3-70b-versatile` | ✅ Optimizer, Cover Letter, Q&A, ATS, Company, Salary, Interview Prep |
| AI (embed) | fastembed `BAAI/bge-small-en-v1.5` | ✅ Local 384-dim, no API key |
| Automation | Playwright + 5 adapters | ✅ Generic, Greenhouse, Lever, Ashby, Workday — all with approval gate |
| Job Sources | Pluggable `JobConnector` | ✅ Greenhouse, Lever, Ashby, SmartRecruiters, Workday, Wellfound |
| Database | PostgreSQL + pgvector | ✅ Migrations 0001-0004; vectors, saved searches, referral tracking |

---

## Phase 1 — ✅ Completed

### 1.1 ✅ Wire AI Services to Groq
- Implemented real LLM calls in `ResumeOptimizer`, `CoverLetterGenerator`, `QuestionAnsweringService` using Groq `llama-3.3-70b-versatile`.
- No-fabrication rule enforced via system prompt.
- New endpoints: `POST /api/v1/ai/optimize-resume`, `/ai/cover-letter`, `/ai/answer-question`.

### 1.2 ✅ Activate Celery Worker Tasks
- `parse_resume` — calls `ResumeParser.parse_with_ai()`, persists `parsed_json` on the Resume row.
- `discover_jobs` — calls the matching `JobConnector`, deduplicates, upserts `Job` rows.
- `match_jobs` — runs `JobMatcher.score()` against user profile.
- `send_notification` — delivers via SMTP when `SMTP_HOST` is configured.
- `sync_email` — placeholder pending Gmail/Outlook OAuth (Phase 1.3).

### 1.3 ✅ Complete Auth Flows (partial)
- Register, login, token refresh implemented and working.
- `forgot-password` and `reset-password` endpoints exist; SMTP delivery wired in worker.
- Google OAuth entry points exist; callback/exchange deferred to Phase 2.

### 1.4 ✅ Implement Remaining Job Connectors
- **Lever** — public posting API (`api.lever.co/v0/postings/{company}`).
- **Ashby** — public job board API (`api.ashbyhq.com/posting-api/job-board/{org}`).
- **SmartRecruiters** — public companies API.
- **Workday** — CXS JSON endpoint with tenant/board pattern.
- **Wellfound** — public job listing endpoint.
- All connectors accept comma-separated company slugs and return validated `JobDTO` objects.

### 1.5 ✅ Build the Web Dashboard
- **Login / Register** pages with token storage.
- **Dashboard** — live analytics stats from API, recent job feed.
- **Profile** page — full CRUD with seniority, summary, preferences, and tech stack selector.
- **Jobs** page — search, discover panel (queues Celery task), apply button.
- **Applications** page — Kanban board by status.
- **Resumes** page — upload, AI parse trigger, LaTeX PDF generation with tech stack tailoring.
- Sidebar with active-route highlighting via Next.js `usePathname`.

### 1.6 ✅ Tech Stack / Field Selection
- User selects a domain field (e.g., "Backend Engineering") and specific tech stacks from curated presets.
- Profile stores `field` and `tech_stacks` columns (migration `0002`).
- Resume generation filters and reorders skills/experience/projects to highlight the selected stack.
- `GET /api/v1/profiles/fields` and `/api/v1/profiles/tech-stacks?field=X` supply the options to the frontend.

### 1.7 ✅ LaTeX Resume Generation
- `LatexResumeService` (`apps/api/app/modules/resumes/latex_service.py`):
  - Jinja2 template with custom `((( )))` delimiters to avoid LaTeX conflicts.
  - All user-supplied strings escaped for LaTeX safety.
  - Skills grouped by category, selected tech stacks promoted to the top.
  - Experience and projects re-sorted by relevance to selected stack.
  - Compiled via `pdflatex` subprocess; PDF bytes streamed back.
- `POST /api/v1/resumes/generate?tech_stacks[]=React` downloads a tailored PDF.
- Dockerfile updated with `texlive-latex-base texlive-latex-extra texlive-fonts-recommended`.

---

## Phase 2 — ✅ Semantic Intelligence

### 2.1 ✅ Vector-Based Job Matching
- **EmbeddingService** (`modules/ai/embedding_service.py`) — local embeddings via `fastembed` + `BAAI/bge-small-en-v1.5` (384-dim, ~130 MB, no API key).
- **Alembic migration 0003** — adds `embedding vector(384)` to `jobs` and `profiles`; creates IVFFlat cosine index on `jobs`.
- **Celery tasks** `embed_job` and `embed_profile` — queued automatically after `discover_jobs` and profile save.
- **JobMatcher** — now combines 60 % cosine similarity + 40 % skill overlap; falls back to skills-only when embeddings absent.
- **`GET /api/v1/ai/semantic-jobs`** — returns jobs ranked by cosine distance to the user's profile embedding.
- fastembed model cache persisted in a named Docker volume (`fastembed-cache`).

### 2.2 ✅ AI-Powered Resume Parsing
- Already implemented in Phase 1 via `ResumeParser.parse_with_ai()` (Groq structured extraction).

### 2.3 ✅ Real ATS Scoring
- **`ATSScoringService`** (`modules/ai/ats_service.py`) — deterministic 5-dimension scorer: keyword match (40 pts), skills overlap (20), action verbs (15), quantified achievements (15), section completeness (10).
- `POST /api/v1/ai/ats-score` — scores the user's latest parsed resume against any job.
- Results include per-dimension breakdown, missing keywords, and actionable suggestions.
- Score displayed in the Job Detail page with a colour-coded progress bar.

### 2.4 ✅ Company Research Service
- **`CompanyResearchService`** (`modules/ai/company_service.py`) — Groq-powered summary from job description context.
- Returns: overview, tech_signals, company_stage, culture_hints, red_flags.
- Summary cached in `Company.summary` on first request.
- `POST /api/v1/ai/company-research` + expandable panel on Job Detail page.

### 2.5 ✅ Salary Intelligence
- **`SalaryEstimationService`** (`modules/ai/salary_service.py`) — Groq estimates min/max/median USD, confidence, reasoning, equity note.
- `POST /api/v1/ai/salary-estimate` — uses profile (YoE, skills) + job (title, location, remote) context.
- Displayed as an expandable panel on the Job Detail page.

### 2.6 ✅ Interview Preparation Assistant
- **`InterviewPrepService`** (`modules/ai/interview_service.py`) — Groq generates behavioral Q+STAR answers, technical questions (with difficulty), questions to ask the interviewer, key talking points, and prep tips.
- `POST /api/v1/ai/interview-prep` — full prep guide for any job × profile pair.
- **`/interview-prep`** page — job ID input, collapsible behavioral cards (with STAR hints), technical question cards (by difficulty), and talking points.
- Linked from Job Detail → "Interview Prep" button and from the Sidebar.

---

## Phase 3 — ✅ Job Application Workflows

### 3.0 ✅ One-Click Auto-Apply
- **`run_automation` Celery task** — launches `BrowserAutomationEngine`, fills form with site-specific adapter, captures screenshot, stores `AutomationTask` as `awaiting_approval`.
- **`submit_application` Celery task** — re-navigates + re-fills + clicks submit after user approval; sets application `status = applied` with `applied_at` timestamp.
- **Full automation router** — `GET/POST /automation/tasks`, `GET /automation/tasks/{id}`, `GET /automation/tasks/{id}/screenshot` (returns base64 PNG), `POST .../approve`, `POST .../cancel`.
- **`/automation` page** — task list panel, form summary JSON, screenshot preview, Confirm/Cancel buttons.

### 3.1 ✅ Saved Job Search Alerts
- **`SavedSearch` model** (migration `0004`) — stores source, query, location, remote_only, score_threshold, interval_hours.
- **`SavedSearchRepository`** with `list_due()` for overdue checks.
- **`process_saved_search` task** — runs connector, upserts jobs, scores against profile embedding, notifies user of high-match jobs.
- **`process_all_saved_searches` task** — scheduled every 6 hours via Celery Beat.
- **Celery Beat service** added to `docker-compose.yml`.
- **`/saved-searches` page** — create/delete/run-now UI with full criteria form.

### 3.2 ✅ Site-Specific Playwright Adapters
- **`GreenhouseSiteAdapter`** — resume upload (`input[type=file]`), all standard fields, custom question labels, EEO section detection.
- **`LeverSiteAdapter`** — `input[name=*]` field map, `cards[*]` custom questions, cover letter textarea.
- **`AshbySiteAdapter`** — `data-testid` field resolution + label-based fallback.
- **`WorkdaySiteAdapter`** — multi-step wizard (up to 6 steps), CAPTCHA detection (halts), auth-wall detection (halts), aria-label matching.
- All adapters registered in `BrowserAutomationEngine._build_default_adapters()`.

### 3.3 ✅ Email-to-Application Status Sync
- **`sync_service.py`** — `classify_email(subject, body)` pattern matcher across 4 stages (interview, offer, rejected, applied).
- Confidence scoring: multiple pattern hits compound; competing signals trigger `requires_review = True`.
- `fetch_recent_emails(provider, access_token)` stub for Gmail + Outlook (Graph API) — ready to activate once OAuth tokens are available.

### 3.4 ✅ Document Export
- **`GET /api/v1/applications/export?format=csv`** — streaming CSV with all application fields.
- **`GET /api/v1/applications/export?format=json`** — GDPR portability bundle (user, profile, resumes metadata, full applications with interview stages and offer details).
- **`/settings` page** — one-click download buttons for both formats.

### 3.5 ✅ Referral Tracking
- `referred_by` and `referral_channel` added to `Application` model and migration `0004`.
- `CreateApplicationRequest` accepts optional referral fields.
- Applications list response includes referral data.
- CSV export includes referral columns.

---

## Phase 4 — Analytics & Market Intelligence

### 4.1 Personal Application Analytics
- **Response rate** — applications sent vs. responses received.
- **Interview funnel** — conversion rate at each stage.
- **Time-to-response** — median days from apply to first response.
- **Match score correlation** — do higher-scored applications convert better?
- **By source** — compare effectiveness across job connectors.

### 4.2 Job Market Trends
- Aggregate skill demand from ingested job descriptions.
- Show "skills in demand this month" and "skills declining" charts.
- Highlight skill gaps between the user's profile and the jobs they are applying for.

### 4.3 Application Velocity Insights
- Suggest optimal daily application volume based on historical funnel data.
- Warn if the user is applying to roles with consistently low match scores.

---

## Phase 5 — Platform & Compliance

### 5.1 Subscription Plans & Billing
- Integrate Stripe Billing with three tiers: **Free** (25 applications/month, manual only), **Pro** (500 applications/month, AI features, automation), **Team** (unlimited, shared profiles, admin seat).
- Enforce per-plan limits in API middleware using Redis counters.
- Build a billing management page: current plan, usage meter, upgrade/downgrade, invoice history.

### 5.2 Rate Limiting
- Implement per-user API rate limiting in Redis (currently configured but not enforced).
- Apply stricter limits on AI generation endpoints and automation start to prevent runaway usage.

### 5.3 Real-Time Updates (WebSockets)
- Add a WebSocket or SSE channel for live automation status updates, match score completions, and email sync results.
- Replace the current polling model in the web dashboard with push updates.

### 5.4 Admin Dashboard
- User management: view, suspend, delete, impersonate.
- Job connector health: last successful sync, error counts, job ingestion rate.
- AI usage and cost monitoring per user and per prompt type.
- Automation audit log viewer.

### 5.5 GDPR & Privacy Compliance
- Implement account deletion: remove all user data, revoke tokens, delete stored files, cascade-delete DB rows.
- Add a data export endpoint (portability) for all user-owned records.
- Cookie consent and privacy policy pages.
- Add a data retention policy: soft-delete email events and audit logs older than 12 months.

### 5.6 Internationalization (i18n)
- Add `next-intl` to the web app for locale-aware text.
- Support locale-specific date/salary formatting.
- Initial locales: `en-US`, `en-GB`, `de-DE`, `fr-FR`.

---

## Phase 6 — Ecosystem Expansion

### 6.1 Browser Extension
- A Chrome/Edge extension that detects job posting pages and surfaces a one-click "Add to AutoApply" button.
- Pre-fills job details from the page into the user's job feed without requiring them to copy/paste the URL.

### 6.2 LinkedIn Integration
- OAuth connection to LinkedIn to import the user's profile (experience, education, skills) as a starting point for profile setup.
- Import saved LinkedIn jobs into the job feed.
- Note: no automation of LinkedIn apply; import only.

### 6.3 Calendar Integration
- OAuth connection to Google Calendar / Outlook Calendar.
- Automatically create calendar events when an interview stage is confirmed (from email sync).
- Show upcoming interviews on the dashboard home page.

### 6.4 Mobile App
- React Native (Expo) app sharing TypeScript DTOs from `packages/shared`.
- Core screens: job feed, application status board, AI generation review, automation approval.
- Push notifications for stage changes and new job matches.

### 6.5 Zapier / Webhook Integrations
- Allow users to configure outbound webhooks on application status changes.
- Pre-built Zapier actions: "New application submitted", "Interview scheduled", "Offer received".
- Useful for connecting to Notion, Airtable, or custom Slack bots.

---

## Technical Debt & Outstanding Items

| Item | Status | Notes |
|---|---|---|
| Google OAuth callback | ⏳ Pending | Entry points exist; token exchange + upsert not yet implemented |
| Email verification flow | ⏳ Pending | Endpoint exists; signed token generation + SMTP send not wired |
| Password reset flow | ⏳ Pending | Endpoint exists; token generation + SMTP send not wired |
| Email sync OAuth | ⏳ Pending | Gmail/Outlook pattern matcher done; OAuth token exchange deferred |
| Tests | ⏳ Pending | E2E Playwright suite configured; unit/integration coverage not yet written |
| S3 file storage | ⏳ Pending | Resume `storage_key` is computed but files are not uploaded to S3 (local only) |
| Rate limiting | ⏳ Pending | Redis configured; per-user API limits not enforced (Phase 5.2) |
| Worker automation queue | ⏳ Pending | `automation` queue not listed in Celery worker `-Q` flag — add it |
