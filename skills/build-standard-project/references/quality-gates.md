# Quality gates

Quality gates are merge and release conditions, not post-release paperwork.

## Root command contract

Expose applicable commands:

```text
pnpm format
pnpm format:check
pnpm lint
pnpm lint:fix
pnpm typecheck
pnpm test
pnpm test:integration
pnpm contract:check
pnpm migration:check
pnpm migration:drift
pnpm build
pnpm test:e2e
pnpm test:cross-browser
pnpm test:a11y
pnpm test:visual
pnpm security:secrets
pnpm security:sast
pnpm security:sbom
pnpm security:audit
pnpm security:audit:toolchain
pnpm validate:requirements
pnpm validate:agent-rules
pnpm validate:no-skipped-critical-tests
pnpm review:ai:check
pnpm review:fingerprint -- <every-material-current-file>
pnpm review:fingerprint -- --base <full-base-sha>
pnpm deploy:preflight
pnpm deploy:smoke
pnpm quality
pnpm quality:full
```

Do not create empty scripts that pretend an unimplemented gate passed. Mark a deferred gate explicitly in the project profile with owner and activation trigger.

`quality` is the required non-browser PR gate. `quality:full` is the AI handoff and release gate and must include browser, accessibility, visual, integration, security, requirement traceability, and AI review validation as applicable.

`security:audit` blocks high or critical vulnerabilities in production dependencies. `security:audit:toolchain` blocks critical vulnerabilities across the full development toolchain. High development-only advisories must be recorded in the AI review with exploitability and upgrade-path analysis; do not apply incompatible transitive overrides merely to silence the scanner.

Unit tests run with coverage enabled; a threshold declaration without `--coverage` and an installed provider is not a gate. Migration validation requires a non-empty migration history, schema validation, CI deployment into a real database, a database-to-schema drift comparison after applying migrations, and integration evidence that the migration ledger is applied without failures. A schema change with no corresponding migration must fail `pnpm migration:drift`.

## Change-specific minimums

| Change | Required evidence |
| --- | --- |
| Documentation | format/lint, links, terminology, traceability |
| UI/component | format, lint, type, unit, accessibility, responsive visual, affected E2E |
| API/contract/event | type, unit, integration, OpenAPI/event compatibility, consumer tests |
| State/permission | domain/property, negative authorization, concurrency, integration, audit |
| Money/points/score | conservation, integer rounding, non-negative, idempotency, reversal, reconciliation |
| Provider | contract fake/recording, timeout, rate limit, retry, dead letter, cost, no false PASS |
| Database migration | validate/generate, empty DB, previous release, data invariants, backfill, recovery |
| Dependency refresh | full gate, SBOM, vulnerability/license scan, migration notes, resolved-version record |
| Product AI | prohibited-input tests, metadata, review, lifecycle, fallback, privacy, incident path |

## Test layers

- Domain: state machines, invariants, permissions, rule snapshots, pure property tests.
- Application: use cases, transactions, idempotency, concurrency, audit, failure compensation.
- API: runtime validation, status/error contract, auth, CSRF, cookies, OpenAPI.
- Repository: real database integration and constraints.
- Worker: duplicate execution, lease recovery, retry, dead letter, replay, provider ambiguity.
- Browser: critical user/operator loops, permission denial, recovery, responsive states.
- Accessibility: axe serious/critical zero, keyboard, focus, names, contrast, reduced motion, screen reader.
- Visual: approved widths, locales, states, and deterministic snapshots.

Use controllable clocks for deadlines, subscriptions, retention, and time-dependent state.

## Coverage and performance

Set project-specific thresholds, with a starting target:

- core domain/application: 85% lines/functions, 75% branches;
- API/contracts and Web testable logic: 75% lines/functions, 65% branches.

Coverage does not replace critical E2E or real-dependency integration tests.

Define budgets for API p95, LCP, INP, CLS, bundle growth, database queries, worker backlog, and provider latency from representative data. Do not prove performance using an empty database.

## CI and release

CI must:

- use frozen dependency installation;
- pin runtime/tool versions and immutable Action revisions where risk warrants it;
- grant minimum permissions and avoid persisted credentials;
- run baseline, static, unit, integration, contract, migration, build, browser, accessibility, visual, and security stages as applicable;
- block Critical/High findings unless an exception has owner, mitigation, approval, and expiry.
- block missing/stale requirement mappings and missing/failed AI review reports.
- reject `.only`, `.skip`, `.fixme`, or equivalent bypasses in required suites.

Release evidence includes migration review, backup/restore rehearsal, configuration completeness, secrets separation, smoke tests, monitoring/alerts, rollback or forward recovery, and a bounded post-release observation window.

Never describe an unrun or failing gate as passing.

Human approval counts must default to zero for VibeCoding repositories. Do not weaken automated or AI review gates to compensate.
