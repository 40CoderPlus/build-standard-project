# Engineering rules

## Repository and change discipline

- Keep root `AGENTS.md` as the canonical AI instruction source. Add tool-specific adapters only when the project actually uses those tools, and keep them as short pointers.
- Preserve unrelated and uncommitted user work. Change only what the current goal requires.
- Reuse existing modules and conventions before adding dependencies or abstractions.
- Record every requirement change, optimization, bug fix, or behavior-affecting maintenance change in the repository's single change record.
- Update directly affected contracts, migrations, docs, and tests with behavior changes.
- Add or update a directly affected test for behavior-source changes. Every bug fix requires a regression test that fails for the reported behavior before the fix and passes afterward.
- Do not stage, commit, push, deploy, rewrite history, or perform other external/destructive actions without authorization.
- Never fabricate a passing check or weaken a test merely to make it green.

## Code and boundaries

- Use the selected language/framework's safe defaults and existing lint/type configuration.
- Validate untrusted input at runtime and keep public contracts independent from persistence/provider types.
- Keep browser code away from databases, private infrastructure SDKs, server configuration, and secrets.
- Keep modules cohesive. Add a new service, package, worker, cache, or queue only when approved behavior needs the boundary.

## Data and security

- Enforce authorization server-side and protect secrets/private data.
- Add idempotency, concurrency control, audit, retention, or recovery behavior where the domain risk requires it; do not scaffold them speculatively for every write.
- Use migrations for schema changes and preserve compatibility or provide an explicit migration path when a public/data contract changes.
- Apply CSRF, CSP, rate limits, upload validation, signed URLs, sanitization, MFA, or immutable audit only to the surfaces that need them.
- Keep real secrets and unnecessary personal data out of Git, logs, fixtures, screenshots, analytics, and browser bundles.

## UI and operations

- Implement the loading, empty, error, permission, retry, responsive, and accessibility states the affected flow actually exposes.
- Keep visible copy and locale handling consistent with the approved product baseline.
- Add logs, metrics, health/readiness, smoke tests, and recovery procedures in proportion to operational risk and the selected deployment model.

## Validation and handoff

- Routine changes: update the concise change record, review the final diff, and run the narrowest relevant affected test.
- Initialization: run the ordinary repository quality baseline once after the scaffold is stable.
- Release/high-risk changes: add only directly affected integration, browser, migration, security, deployment, or independent-review evidence.
- Report the outcome, checks actually run, material risk, and required next action. Keep routine handoffs short.
