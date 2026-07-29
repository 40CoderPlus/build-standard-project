# Engineering rules

## Repository authority

- Make root `AGENTS.md` canonical for humans and AI tools.
- Make tool-specific instruction files point to `AGENTS.md`; do not duplicate business rules.
- Preserve approved product, architecture, API, database, design, and quality baselines with an explicit authority order.
- Update code, contracts, migrations, documentation, traceability, and tests together when behavior changes.
- Assign a stable requirement/optimization ID before changing behavior and keep acceptance, tests, AI review, and release evidence linked.

## Change discipline

- Inspect repository state and preserve unrelated or uncommitted user changes.
- Modify only what the current goal requires.
- Prefer reuse and extension over parallel modules or rewrites.
- Do not add dependencies without documenting need, alternatives, maintenance, license, bundle/runtime cost, and security impact.
- Do not stage, commit, amend, rebase, push, tag, or rewrite history unless explicitly requested.
- Never bypass hooks or CI, fabricate results, or lower a threshold to make a failure green.
- Require an independent AI review for every material change. Human review is optional and non-blocking unless explicit external authority requires it.

## TypeScript and boundaries

- Enable `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, and fallthrough protection.
- Reject explicit `any`; validate `unknown` at boundaries.
- Use consistent package aliases and type-only imports.
- Keep contracts independent of frameworks, Prisma, Node-private APIs, and provider SDKs.
- Keep browser code from importing database clients, AWS/private infrastructure SDKs, server configuration, or secrets.
- Enforce package boundaries in ESLint.

## API and state

- Validate DTOs at runtime.
- Declare authorization, idempotency, concurrency control, transaction, audit, and stable errors for every write endpoint.
- Use optimistic locking or an equivalent rule where concurrent editing can lose data.
- Verify webhook signatures, deduplicate event IDs, tolerate out-of-order delivery, and make consumers idempotent.
- Version breaking API/event changes and provide migration/compatibility behavior.
- Do not return provider errors as successful domain outcomes.

## Configuration and secrets

- Validate configuration at startup and fail closed for missing critical values.
- Keep `.env.example` complete but limited to names, documentation, and fake values.
- Keep secrets out of Git, logs, snapshots, OpenAPI examples, analytics, and browser bundles.
- Limit `NEXT_PUBLIC_*` to deliberately public configuration.
- Version business rules as data/configuration. Freeze rule snapshots for open workflows so future configuration does not rewrite history.

## Security, privacy, and audit

- Enforce authorization server-side with authentication, RBAC, ownership, entitlement/certification, and task grants as required.
- Apply input validation, output encoding, CSP, CSRF, rate limits, upload validation, signed URLs, and HTML sanitization as relevant.
- Use individual admin identities, MFA when risk requires it, re-authorization, reason capture, and immutable audit for sensitive actions.
- Do not log tokens, secrets, full private content, payment data, tax/bank identity, hidden review relations, or unnecessary PII.
- Define retention, deletion, export, withdrawal, recovery, and legal hold behavior.

## UI and internationalization

- Treat the approved design system as the token authority; use shadcn/ui for behavior and structure, not generic branding.
- Implement loading, empty, error, permission, processing, success, disabled, hover, focus, destructive, retry, cancel, and degraded states as applicable.
- Keep visible copy in locale dictionaries. Maintain functional and numeric equivalence across supported locales.
- Meet WCAG 2.2 AA for supported flows: semantic names, keyboard navigation, visible focus, contrast, screen-reader behavior, reduced motion, and non-color state cues.
- Define responsive evidence at representative mobile, tablet, and desktop widths.
- Do not recompute authoritative public metrics, ranks, balances, or permissions in browser components.

## Observability and operations

- Use structured logs with request/trace/job IDs and stable error codes.
- Separate expected 4xx user errors from 5xx system failures; keep internal causes out of public responses.
- Track latency, error rate, dependency failures, database/query health, job backlog, retries, dead letters, upload failures, and domain-critical outcomes.
- Provide health/readiness checks, migration procedure, rollback/forward recovery, backup restore evidence, and smoke tests.

## Git quality

- Use Conventional Commits: `<type>(<scope>)!: <imperative English summary>`.
- Keep each change focused on one coherent intent.
- Keep dependency refreshes and repository-wide formatting separate.
- Commit generated artifacts with their source/schema and review their diffs.
- A valid handoff reports outcome, changed files/behavior, migrations/configuration, checks and exact results, untested areas, risks, and next action.
- A valid handoff includes the AI review report, resolved findings, deployment/smoke evidence when released, and requirement status.
