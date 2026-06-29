"""
Email-to-application status sync service.
Parses email subject/body for stage-change signals and updates Application.status.
Requires Gmail or Outlook OAuth tokens (Phase 3.3 — token exchange deferred to auth Phase 2).
"""
import re
from dataclasses import dataclass


# --- Pattern definitions ---

@dataclass
class StageSignal:
    status: str
    patterns: list[str]
    confidence_weight: float  # how strongly each match counts (0-1)


_SIGNALS: list[StageSignal] = [
    StageSignal("interview", [
        r"invite.*interview", r"interview.*invitation", r"schedule.*interview",
        r"phone\s+screen", r"technical\s+screen", r"onsite", r"virtual\s+interview",
        r"we.{0,20}like\s+to\s+chat", r"schedule\s+a\s+call", r"next\s+steps",
        r"moving\s+forward", r"move\s+forward",
    ], 0.8),
    StageSignal("offer", [
        r"offer\s+letter", r"pleased\s+to\s+offer", r"compensation\s+package",
        r"accept\s+the\s+offer", r"offer\s+of\s+employment", r"congratulations.*offer",
        r"welcome\s+to\s+the\s+team",
    ], 0.95),
    StageSignal("rejected", [
        r"unfortunately", r"not\s+moving\s+forward", r"decided\s+not\s+to",
        r"other\s+candidates", r"not\s+selected", r"position\s+has\s+been\s+filled",
        r"will\s+not\s+be\s+moving", r"regret\s+to\s+inform", r"not\s+a\s+fit",
    ], 0.9),
    StageSignal("applied", [
        r"received\s+your\s+application", r"application\s+received",
        r"thank\s+you\s+for\s+applying", r"application\s+has\s+been\s+submitted",
    ], 0.7),
]

_CONFIDENCE_THRESHOLD = 0.5
_AMBIGUOUS_THRESHOLD = 0.3


@dataclass
class SyncResult:
    suggested_status: str | None
    confidence: float
    matched_patterns: list[str]
    requires_review: bool
    raw_signals: dict[str, float]


def classify_email(subject: str, body: str) -> SyncResult:
    """
    Classify an email into an application status signal.
    Returns SyncResult with confidence scores and review flag.
    """
    text = f"{subject} {body}".lower()
    scores: dict[str, float] = {}

    for signal in _SIGNALS:
        matches = [p for p in signal.patterns if re.search(p, text)]
        if matches:
            # Multiple pattern matches increase confidence (capped at 1.0)
            raw = min(len(matches) * signal.confidence_weight, 1.0)
            scores[signal.status] = raw

    if not scores:
        return SyncResult(None, 0.0, [], False, {})

    best_status = max(scores, key=lambda k: scores[k])
    best_score = scores[best_status]
    matched = [p for sig in _SIGNALS if sig.status == best_status for p in sig.patterns if re.search(p, text)]

    requires_review = (
        best_score < _CONFIDENCE_THRESHOLD
        or len(scores) > 1  # competing signals
    )

    return SyncResult(
        suggested_status=best_status if best_score >= _AMBIGUOUS_THRESHOLD else None,
        confidence=round(best_score, 2),
        matched_patterns=matched[:5],
        requires_review=requires_review,
        raw_signals={k: round(v, 2) for k, v in scores.items()},
    )


# --- Stub email fetcher (requires OAuth tokens) ---

async def fetch_recent_emails(provider: str, access_token: str, since_hours: int = 24) -> list[dict]:
    """
    Fetch recent emails from Gmail or Outlook.
    Requires OAuth2 access token for the respective provider.
    Returns list of {message_id, subject, body, from, date}.
    """
    if provider == "gmail":
        return await _fetch_gmail(access_token, since_hours)
    if provider == "outlook":
        return await _fetch_outlook(access_token, since_hours)
    raise ValueError(f"Unsupported email provider: {provider}")


async def _fetch_gmail(access_token: str, since_hours: int) -> list[dict]:
    """Fetch Gmail messages via Google People API."""
    import httpx
    from datetime import UTC, datetime, timedelta
    after_ts = int((datetime.now(UTC) - timedelta(hours=since_hours)).timestamp())
    headers = {"Authorization": f"Bearer {access_token}"}
    messages = []
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers=headers,
            params={"q": f"after:{after_ts}", "maxResults": 50},
        )
        resp.raise_for_status()
        for msg in resp.json().get("messages", []):
            detail = await client.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
                headers=headers,
                params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
            )
            detail.raise_for_status()
            d = detail.json()
            headers_list = d.get("payload", {}).get("headers", [])
            subject = next((h["value"] for h in headers_list if h["name"] == "Subject"), "")
            messages.append({
                "message_id": msg["id"],
                "subject": subject,
                "body": d.get("snippet", ""),
                "provider": "gmail",
            })
    return messages


async def _fetch_outlook(access_token: str, since_hours: int) -> list[dict]:
    """Fetch Outlook messages via Microsoft Graph API."""
    import httpx
    from datetime import UTC, datetime, timedelta
    since = (datetime.now(UTC) - timedelta(hours=since_hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            "https://graph.microsoft.com/v1.0/me/messages",
            headers=headers,
            params={"$filter": f"receivedDateTime ge {since}", "$top": 50, "$select": "id,subject,bodyPreview"},
        )
        resp.raise_for_status()
        return [
            {
                "message_id": m["id"],
                "subject": m.get("subject", ""),
                "body": m.get("bodyPreview", ""),
                "provider": "outlook",
            }
            for m in resp.json().get("value", [])
        ]
