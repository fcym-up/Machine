# ADR-0002: API Key Authentication for Protected Endpoints

## Status
Accepted

## Context
Project Machine is a personal AI system. All /api/v1/* endpoints were previously
accessible without any authentication, which poses a security risk on networks
where the service is exposed.

## Decision
Use a simple API Key-based authentication for all /api/v1/* endpoints.

- API key stored in .env as MACHINE_API_KEY
- Validation via FastAPI dependency injection
- X-API-Key header required for all protected routes
- Public endpoints: GET /, /docs

## Alternatives Considered

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| API Key | Simple, no user management needed | No multi-user support | Selected - matches personal-system nature |
| JWT | Multi-user, expiry support | Over-engineered for single user | Rejected |
| No auth | Zero friction | Security risk on networks | Rejected |

## Consequences
- All API routes now require X-API-Key header
- Default dev key: "machine-dev-key-change-me"
- Future: upgrade to JWT if multi-user support needed
