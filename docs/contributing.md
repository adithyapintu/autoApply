# Contributing

## Development Principles

- Keep routers thin and push business logic into services.
- Introduce connectors through the shared connector interface.
- Add tests for services, repositories, and route behavior.
- Keep AI prompts versioned and documented.
- Never merge automation changes that can submit without user confirmation.

## Test Commands

```bash
cd apps/api && pytest
pnpm typecheck
pnpm build:web
pnpm test:e2e
```

