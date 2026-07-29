# Architecture and stack

## Standard topology

```text
Browser
  → Next.js Web/Admin
  → NestJS modular-monolith REST API
  → PostgreSQL
  → S3-compatible object storage
  → Worker for background jobs
```

Use a pnpm + Turborepo monorepo:

```text
apps/
  web/
  api/
  worker/       # conditional
  admin/        # conditional
packages/
  config/
  contracts/
  domain/
  db/
  ui/
  observability/
  testkit/
  sdk/          # conditional
  redis/        # conditional
docs/
  product/
  architecture/
  engineering/
```

Apps must not import another app's source. Shared code belongs in packages. Keep dependency direction toward pure contracts/domain packages.

## Web

- Use Next.js App Router, React, TypeScript, Tailwind CSS, and shadcn/ui/Radix.
- Default to React Server Components. Push `"use client"` to the smallest browser-interaction boundary.
- Use a shared API client; do not scatter raw `fetch`, paths, errors, cookies, CSRF, or request IDs through components.
- Keep server authority out of global client state. Prefer server data, local React state, and explicit browser adapters.
- Release browser resources: streams, audio nodes, object URLs, animation frames, observers, and listeners.
- Use design tokens rather than page-local colors, spacing, type, radii, shadows, or z-index values.

## API and domain

- Use REST `/api/v1` and OpenAPI.
- Controller: HTTP mapping, validated DTO, response metadata.
- Application: use cases, authorization after authentication, transaction, idempotency, audit.
- Domain: entities, value objects, policies, state machines, errors; no NestJS or Prisma dependency.
- Infrastructure: Prisma repositories and provider adapters.
- Do not let one module write another module's tables directly.
- Expose stable wire contracts, not persistence models.
- Use RFC 9457 Problem Details or one equally consistent documented error contract.

## Data

- Default to UUIDv7 or a documented sortable UUID policy, UTC timestamps, explicit uniqueness and indexed foreign keys.
- Use integer minor units for money and basis points for ratios.
- Put state transitions behind domain commands; record actor, reason, old/new state, time, and rule/config snapshot.
- Use append-only correction/reversal records for financial, points, score, audit, and published-revision facts when present.
- Apply every schema change through a migration. Use expand → backfill → switch → contract for destructive evolution.
- Do not perform external calls inside a database transaction.

## Background work

Choose the lowest sufficient tier:

1. **No worker**: request-bound work is short, local, and safely retryable.
2. **PostgreSQL Job**: bounded background work; claim with leases and `SKIP LOCKED`, run providers outside the claim transaction, retry with backoff, then dead-letter.
3. **Transactional Outbox + queue**: durable external delivery or independent consumers are required. Commit business state and outbox atomically; make consumers idempotent.

Redis may provide cache, rate limits, and short locks. It never owns balances, permissions, publication, audit, or other business truth.

## Storage and uploads

- Generate object keys server-side.
- Use presigned upload intents and completion confirmation.
- Verify existence, size, media type, hash, scan status, rights, review, and publication state.
- Prefer one bucket with fixed `temp/`, `private/`, `quarantine/`, `published/`, and `archive/` prefixes unless infrastructure requires stronger isolation.
- Public URL availability never substitutes for authorization or publication status.

## Escalation triggers

Require an ADR before adding:

- microservices or independent database ownership;
- Kafka, Kubernetes, distributed saga, GraphQL, or OpenSearch;
- a global client state library;
- a second source of product configuration;
- a new authentication framework or provider;
- a new AI provider/model class;
- a second object-storage authority;
- runtime dependency on experimental/preview features.
