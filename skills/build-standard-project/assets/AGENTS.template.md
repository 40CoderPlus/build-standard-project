# {{PROJECT_DISPLAY_NAME}} repository instructions

This is the canonical instruction source.

## Route

The Routine path is the default for scoped fixes, optimizations, UI changes, and refactors. Read only relevant code, tests, contracts, and instructions. Use Full only for initialization, release, or affected security/privacy, money/data, migration/public-contract, shared-infrastructure, deployment, or product-AI boundaries.

## Execute

- Treat efficiency as part of quality. Do safe in-scope work without an upfront plan, repeated confirmation, or step narration. Batch one question only when a decision materially changes behavior, architecture, cost, or risk.
- Preserve unrelated work and make the smallest coherent change.
- Append one concise entry to `docs/changes.md` for every requirement change, optimization, bug fix, or behavior-affecting maintenance change. Keep this as the only change ledger.
- `.project/standard-project.json` records the user's technology/deployment choice. Prefer minimum sufficient design; never add complex infrastructure without explicit user selection. After material risks are disclosed, the user owns the approved product/architecture/operations tradeoff.
- Read task-relevant product/engineering documents only when the affected boundary requires them. Do not invent product rules.
- Keep browser code away from databases/secrets, validate external input, enforce authorization server-side, and protect real secrets/private data.
- Do not perform destructive Git/filesystem actions, commits, pushes, deployments, or external writes without authorization.

## Validate

- Every behavior-affecting source change must add or update a directly affected test and cite that test in `docs/changes.md`. Every bug fix must add a regression test that reproduces the failure before the fix and passes after it.
- Routine: run the directly affected test file, for example `pnpm test -- path/to/affected.test.ts`, then review the final diff. Do not run `pnpm quality`, `pnpm quality:full`, coverage, E2E, visual, deployment, or independent-review checks for an ordinary scoped change. Use `pnpm quality:fast` only when no narrower unit-test command exists or broader unit feedback is explicitly needed.
- CI runs `pnpm change:check` and the unit-test suite. Add other checks only for an affected risk or explicit request.
- Full: run directly affected integration, browser, security, migration, and deployment checks. Request an independent review only when risk or policy warrants it.
- Do not rerun unaffected successful checks or fabricate evidence. Keep human review optional unless explicitly required.

## Finish

Stop when the change record and affected test are current, the direct test passes, and the final diff is reviewed. Report only outcome, key evidence, and material risk or required user action.
