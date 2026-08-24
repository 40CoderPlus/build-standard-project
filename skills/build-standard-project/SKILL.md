---
name: build-standard-project
description: Initialize or standardize a project only on explicit init requests, then keep routine maintenance fast. During init, recommend the minimum sufficient technology/deployment options, require the user's choice, and never add complex infrastructure without explicit approval.
---

# Build Standard Project

Version: **1.6**

## Route

- **Routine (default):** scoped bug, optimization, UI change, or refactor. Use the fast path below.
- **Init/adopt:** only when explicitly asked to initialize, scaffold, standardize, adopt, or rebuild. Read [init-workflow.md](references/init-workflow.md).
- **Audit:** report prioritized gaps; do not modify unless asked.
- **Release:** read [quality-gates.md](references/quality-gates.md), [ai-review-system.md](references/ai-review-system.md), and [deployment-system.md](references/deployment-system.md). Do not repeat Init.

Do not upgrade Routine to Init because this skill or its generated rules exist in the repository.

## Work style

- Keep the quality floor: the smallest coherent change, final-diff review, the narrowest relevant test, and honest reporting.
- Treat efficiency as part of quality. Anything beyond that floor needs affected-risk evidence or an explicit user request; unnecessary process, architecture, deliberation, narration, and repeated validation are defects.
- Infer reversible details. Ask only when a missing decision materially changes behavior, architecture, cost, or risk; batch it once with a recommendation.
- Once decided, execute. Reopen a decision only when new evidence makes it invalid.
- Prefer the minimum sufficient design. Do not propose or implement a more complex component unless simpler options are inadequate for an approved product requirement.
- Redis, queues, workers, separate APIs, search clusters, microservices, Kubernetes, multi-region, or similar complexity require explicit user selection before implementation.
- After material costs, limits, and risks are stated, the user owns the selected product/architecture/operations tradeoff. AI still owns truthful disclosure and correct in-scope implementation; this is not permission to hide known risk or bypass safety/legal constraints.

## Routine fast path

1. Inspect only relevant code, tests, contracts, and root instructions.
2. Make the smallest coherent change and preserve unrelated work.
3. Review the final diff.
4. Run the narrowest relevant unit test; add only directly affected checks.
5. Rerun only a failed check or one invalidated by later edits.

Routine work does not require a REQ/OPT record, independent reviewer, AI-review artifact, aggregate quality gate, E2E/visual suite, deployment evidence, or long handoff unless the user explicitly asks.

Expand validation only for the affected boundary: security/privacy, money/entitlements, irreversible data, migration/public contract, shared infrastructure, deployment, or product-AI governance. Full traceability and independent review apply only when high-risk, release-bound, or explicitly required.

## Finish

Stop when the requested outcome passes proportionate checks. Reply with only the outcome, key test/review evidence, and material risk or required user action. Never weaken checks or fabricate evidence.
