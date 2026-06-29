# AI Package

This package stores prompt templates and AI service contracts. Runtime service classes live in `apps/api/app/modules/ai` so they can use API configuration, logging, tracing, and persistence.

## Required Guardrails

- Use only user-provided candidate facts and job/company input.
- Refuse to invent missing qualifications.
- Return structured JSON for machine workflows.
- Mark generated application content as requiring user review.
- Keep prompt versions stable and auditable.

