# Quality gates

Quality gates are proportional to the selected route. Routine work optimizes for fast feedback; initialization, high-risk work, and releases use broader gates.

## Root command contract

Expose consistent root commands using the selected ecosystem. The following names are the pnpm/TypeScript implementation used by the bundled modular-monolith generator; adapt them rather than forcing pnpm onto another approved stack:

```text
pnpm format
pnpm format:check
pnpm lint
pnpm lint:fix
pnpm typecheck
pnpm test
pnpm quality:fast
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

`quality:fast` is the routine path and should run relevant unit tests with the repository's cheapest directly affected static check. Agents may invoke a narrower package/test command when it is more focused.

`quality` is the initialization and broad non-browser gate. `quality:full` is the release/high-risk gate and includes browser, accessibility, visual, integration, security, requirement traceability, and AI-review validation as applicable. Do not run either aggregate gate for an ordinary scoped fix unless requested.

## Execution budget

- Efficiency is part of quality. Checks beyond the routine floor require an affected risk or explicit user request.
- Routine: review the final diff, run the narrowest relevant unit test once, and add only a directly affected static/integration check.
- After a failure, fix and rerun that check. Do not restart unrelated successful checks.
- If an aggregate gate will rerun targeted checks, run it once after implementation is stable rather than repeatedly during editing.
- Stop when the selected route's required checks pass and no material review finding remains.

`security:audit` blocks high or critical vulnerabilities in production dependencies. `security:audit:toolchain` blocks critical vulnerabilities across the full development toolchain. High development-only advisories must be recorded in the AI review with exploitability and upgrade-path analysis; do not apply incompatible transitive overrides merely to silence the scanner.

Unit tests run with coverage enabled; a threshold declaration without `--coverage` and an installed provider is not a gate. Migration validation requires a non-empty migration history, schema validation, CI deployment into a real database, a database-to-schema drift comparison after applying migrations, and integration evidence that the migration ledger is applied without failures. A schema change with no corresponding migration must fail `pnpm migration:drift`.

## Risk-triggered minimums

For routine documentation, UI, and code fixes, review the final diff and run relevant unit tests; add only directly affected checks. Use the table when a change crosses the listed risk boundary or is part of initialization/release work.

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

Full/release CI must:

- use frozen dependency installation;
- pin runtime/tool versions and immutable Action revisions where risk warrants it;
- grant minimum permissions and avoid persisted credentials;
- run baseline, static, unit, integration, contract, migration, build, browser, accessibility, visual, and security stages as applicable;
- block Critical/High findings unless an exception has owner, mitigation, approval, and expiry.
- block missing/stale requirement mappings and missing/failed AI review reports when those artifacts are required by the route.
- reject `.only`, `.skip`, `.fixme`, or equivalent bypasses in required suites.

Release evidence includes migration review, backup/restore rehearsal, configuration completeness, secrets separation, smoke tests, monitoring/alerts, rollback or forward recovery, and a bounded post-release observation window.

Never describe an unrun or failing gate as passing.

Routine pull-request CI should favor `quality:fast`; schedule or trigger `quality:full` for main-branch integration, high-risk labels, initialization baselines, and releases. Human approval counts default to zero for VibeCoding repositories. Do not weaken a gate that the selected route actually requires.
