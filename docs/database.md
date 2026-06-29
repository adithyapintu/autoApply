# Database Schema

```mermaid
erDiagram
  USERS ||--o| PROFILES : owns
  PROFILES ||--o{ SKILLS : has
  PROFILES ||--o{ EXPERIENCE : has
  PROFILES ||--o{ EDUCATION : has
  PROFILES ||--o{ PROJECTS : has
  USERS ||--o{ RESUMES : uploads
  RESUMES ||--o{ RESUME_VERSIONS : produces
  COMPANIES ||--o{ JOBS : posts
  USERS ||--o{ APPLICATIONS : tracks
  JOBS ||--o{ APPLICATIONS : receives
  RESUME_VERSIONS ||--o{ APPLICATIONS : uses
  APPLICATIONS ||--o{ AUTOMATION_TASKS : runs
  USERS ||--o{ NOTIFICATIONS : receives
  USERS ||--o{ EMAIL_EVENTS : syncs
  USERS ||--o{ AUDIT_LOGS : triggers
```

The transactional schema is normalized for application workflows. Embedding columns and pgvector indexes should be added once production embedding dimensions are finalized for the selected OpenAI embedding model.

