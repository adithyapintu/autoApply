# Security Review

## Controls

- Passwords use Argon2id plus application-level pepper.
- Access and refresh JWTs use different secrets and TTLs.
- Refresh tokens are hashed before storage.
- Resumes and generated documents should be envelope-encrypted before object storage.
- OAuth scopes must be least-privilege and provider reviewed.
- Audit logs record auth, profile changes, AI generation, automation checkpoints, approval, and submission.
- Rate limiting applies by IP and user id.
- File uploads validate MIME type, extension, size, and parser behavior.
- Browser automation never bypasses CAPTCHAs or anti-bot flows.
- User confirmation is mandatory before final submission.

## Production Hardening Checklist

- Rotate all `.env` secrets into a managed secret store.
- Enable TLS everywhere and HTTP security headers in Nginx.
- Configure CSRF protection for cookie-based sessions if introduced.
- Turn on database backups and point-in-time recovery.
- Configure S3 bucket encryption, versioning, and blocked public access.
- Configure OpenTelemetry traces, structured logs, and alerting.
- Run SAST, dependency scanning, container scanning, and migration checks in CI.

