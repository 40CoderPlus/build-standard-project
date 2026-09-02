# Quality checks

Quality checks are proportional to the selected route. Keep the default path fast and add checks only for a boundary the change actually affects.

## Command contract

The bundled pnpm/TypeScript generator always exposes the core commands and adds the optional suite commands only when the profile activates them:

```text
pnpm format
pnpm format:check
pnpm lint
pnpm lint:fix
pnpm typecheck
pnpm test
pnpm quality:fast
pnpm change:check -- --base <sha>
pnpm contract:check
pnpm migration:check
pnpm migration:drift
pnpm build
pnpm test:integration
pnpm test:e2e
pnpm test:cross-browser
pnpm test:a11y
pnpm test:visual
pnpm security:audit
pnpm security:audit:toolchain
pnpm deploy:preflight
pnpm deploy:smoke
pnpm quality
pnpm quality:full
```

Adapt these concepts to another approved stack instead of forcing pnpm onto it. Do not create empty scripts that pretend an unavailable check passed.

- For local Routine work, run the directly affected test file first, such as `pnpm test -- path/to/affected.test.ts`. Do not replace it with an aggregate command merely because that command is easier to remember.
- `quality:fast` runs the unit-test suite for CI or broader unit feedback. It is a fallback, not the default local command for a scoped Bug.
- `change:check` is the lightweight traceability check: a product or behavior-source change must add a `docs/changes.md` entry, change a directly affected test, and cite that test. A bug entry must cite its regression test.
- `quality` is the ordinary repository baseline: formatting, lint, types, unit tests, contracts, migration structure, and build.
- `quality:full` adds configured integration/browser/accessibility/visual checks, migration drift, dependency audits, and deployment preflight. Use it for release or affected high-risk boundaries, not ordinary edits.

Policy-specific security and supply-chain evidence belongs to the selected hosting or compliance workflow. Do not scaffold hand-written generic scanners or review-binding machinery.

## Execution budget

- Routine: run the directly affected unit-test file once and review the final diff. Do not run `quality`, `quality:full`, coverage, E2E, visual, deployment, or independent review for an ordinary scoped change.
- Add a static, integration, browser, migration, or security check only when the changed boundary warrants it.
- After a failure, fix and rerun that check. Do not restart unrelated successful checks.
- Run an aggregate command once after the implementation is stable when it adds useful coverage.
- Stop when required checks pass and no material review finding remains.

## Risk-triggered checks

| Boundary | Add when affected |
| --- | --- |
| UI/component | type/unit, accessibility, responsive or E2E evidence for changed states |
| API/public contract | contract compatibility, integration, consumer behavior |
| Authorization/state | negative authorization, state invariants, concurrency or audit tests |
| Money/entitlements | rounding/conservation, idempotency, reversal and reconciliation |
| Database migration | empty/current database migration, invariants, backfill and recovery |
| Provider/async work | timeout, retry, duplicate delivery, fallback and failure visibility |
| Dependency/toolchain | production audit and any policy-required license or supply-chain scan |
| Deployment | preflight, health/readiness, smoke and rollback/forward recovery |
| Product AI | prohibited inputs, privacy/consent, provenance, review and fallback |

Coverage and performance budgets should come from product risk and representative data. A generic percentage or empty-database benchmark is not proof of quality.

## CI and release

Routine pull-request CI should run `change:check` and the fast test path. This establishes the presence and linkage of the record and test; final-diff review still checks whether they truthfully cover the behavior. Run broader checks manually or on release/high-risk workflows. Use frozen dependency installation, pinned runtimes, minimum permissions, and honest failure reporting.

Release evidence should be proportional to the target: migration and configuration readiness, secrets separation, health/smoke results, and recovery instructions. Production deployment remains an external side effect requiring user authorization.

Never describe an unrun or failing check as passing.
