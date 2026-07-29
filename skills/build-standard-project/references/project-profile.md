# Project profile

Create `.project/standard-project.json` as the machine-readable record of generation decisions. Start from `assets/project-profile.example.json`.

## Required fields

- `schemaVersion`
- `project.name`, `displayName`, `packageScope`, `description`
- `product.phase`, `sourceOfTruth`, `locales`, `defaultLocale`
- `runtime.node`, `pnpm`, `typescript`
- `web.enabled`, `next`, `react`, `tailwind`, `designSystem`
- `api.enabled`, `nest`, `adapter`, `basePath`
- `data.database`, `databaseVersion`, `prisma`
- `apps.admin`, `apps.worker`
- `async.mode`, `redis`
- `storage.mode`
- `auth.mode`
- `deployment.mode`, `deployment.environments`
- `quality`
- `review.aiRequired`, `review.humanRequired`
- `decisions`

## Selection policy

Use exact versions. Treat the bundled example as a tested baseline snapshot, not an eternal “latest” claim.

Default choices:

- PostgreSQL unless approved hosting, migration, or organizational constraints require MySQL.
- Fastify for a new NestJS API unless a required integration has a documented Express dependency.
- Default `apps.worker` to false. Enable PostgreSQL Job + Worker only when an approved requirement defines a real handler, lifecycle, retry/replay, lease/dead-letter, and health contract; never deploy an empty keepalive worker.
- Transactional Outbox + SQS when external delivery, independent scaling, or durable cross-process events are already required.
- No Redis until caching, rate limiting, or short distributed locks are required.
- No dedicated admin app until operator surface, isolation, or deployment requirements justify it.
- Identity adapter boundary always; choose Better Auth only after session, provider, account-linking, and deployment requirements are known.
- S3-compatible storage only when the product owns binary assets.
- Container-generic deployment assets by default; select a cloud adapter only when the target is known.
- Mandatory independent AI review and optional human review for normal VibeCoding.

## Decision records

Each `decisions` entry contains:

```json
{
  "id": "ADR-001",
  "status": "accepted",
  "classification": "default",
  "decision": "Use a modular monolith",
  "reason": "MVP requires one deployable domain boundary and has no proven independent scaling need",
  "revisitWhen": "A measured workload or ownership boundary requires independent deployment"
}
```

Never hide a deferred decision in code comments. Put the trigger and owner in the profile or an ADR.
