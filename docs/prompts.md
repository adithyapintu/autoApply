# Prompt Documentation

Every AI service has an independent prompt and a strict factuality boundary.

## Global Rules

- Use only facts found in the candidate profile, resume, user-provided notes, or job description.
- Never invent skills, degrees, employment, metrics, links, dates, salary history, visa status, or achievements.
- When information is missing, ask a follow-up question or produce a conservative placeholder marked for user review.
- Return structured JSON where the API expects machine-readable output.

## Services

- Resume parser
- Skill extractor
- Candidate profile generator
- Job matcher
- Resume optimizer
- Cover letter generator
- Question answering
- Application summarizer
- Company summarizer
- Salary estimation
- Interview preparation

