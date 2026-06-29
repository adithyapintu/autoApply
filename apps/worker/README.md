# Worker App

Celery workers are implemented in `apps/api/app/worker.py` so they can share domain services, Pydantic schemas, repositories, and configuration with the API process.

Recommended production queue split:

- `parsing`: resume OCR and document parsing
- `discovery`: connector-based job discovery
- `ai`: matching, generation, summarization, interview prep
- `email`: Gmail and Outlook sync
- `notifications`: email, Slack, Discord, Telegram, push
- `automation`: browser automation jobs that stop at approval checkpoints

Scale each queue independently based on runtime cost and provider rate limits.

