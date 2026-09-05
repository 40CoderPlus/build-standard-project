# Initialization workflow

Read only for explicit Init/adoption.

## 1. Establish inputs

Read [product-handoff.md](product-handoff.md), approved product/design/contracts, and existing repository rules. Infer product scale, risk, workload, budget, team, operations, and deployment constraints. Ask one batched question only for gaps that change architecture; otherwise proceed with stated assumptions.

Stop and report a conflict only when authoritative sources disagree on behavior, permissions, money, privacy/data, AI boundaries, or release scope.

## 2. Get one user decision

Read [architecture-and-stack.md](architecture-and-stack.md). Normally present two choices:

1. the minimum sufficient option (recommended);
2. the next justified option, only if a real requirement could need it.

Show relative delivery speed, cost/operations, limits, material risks, and upgrade trigger. Show a complex third option only when approved requirements already justify it. AI must not select or implement complex infrastructure without explicit user approval.

After risks are disclosed, the user owns the selected product/architecture/operations tradeoff. Record `user-approved`; use `user-delegated` only when the user explicitly says AI may decide, then choose the minimum sufficient option. Do not reopen the choice without new evidence.

## 3. Build the selected foundation

Read [project-profile.md](project-profile.md) and record considered/selected options, selection mode, rejected alternatives, and revisit triggers in `.project/standard-project.json`.

Every selected architecture must include the same non-configurable engineering baseline from initialization: repository-local commit hooks for staged format/lint and Conventional Commits, one concise change record, directly affected tests, Bug regression tests, and CI/release commands appropriate to the stack. Generate these with the foundation; do not defer them until feature work or ask the user to select them as optional tooling.

The bundled generator supports only user-approved `modular-monolith` + `container-generic`:

```text
python scripts/scaffold_project.py --config <approved-profile.json> --output <target>
pnpm install
pnpm format
pnpm quality
```

For another selected option, generate it directly or extend the generator; never change the profile to fit the template. Use [generation-contract.md](generation-contract.md) for outcomes and [engineering-rules.md](engineering-rules.md), [ai-rules.md](ai-rules.md), [quality-checks.md](quality-checks.md), and [deployment-system.md](deployment-system.md) only as applicable to the chosen stack. Preserve one canonical root `AGENTS.md` and the Routine fast path.

## 4. Verify once

Implement one representative vertical slice with observable acceptance criteria: successful user outcome, relevant failure state, and permission boundary when applicable. For a UI slice, inspect the actual affected screen and interaction when feasible; report unavailable verification explicitly. Add its concise record and affected test as described in [product-change-notes.md](product-change-notes.md), then run `pnpm quality` once after implementation stabilizes. Add only checks justified by the slice's affected boundaries. Use [independent-review.md](independent-review.md) only for release, high-risk boundaries, or an explicit request.

Report the selected option, delivered foundation, checks, material findings/gaps, and required user action. Omit process narration.
