---
name: build-standard-project
description: Turn an approved product design, PRD, prototype, design system, or architecture brief into an AI-governed, deployable full-stack project with a pnpm monorepo, requirement traceability, canonical multi-agent rules, mandatory AI review, executable quality gates, CI, container deployment assets, and handoff evidence. Use when Codex is asked to initialize, scaffold, standardize, template, refresh, or rebuild a web product repository after product design; to create project-wide engineering and AI rules; or to align an existing project with the shared PinChina, ResonA, and ThreadInk engineering model. Do not use for a small isolated code change that does not establish or revise project-wide foundations.
---

# Build Standard Project

Convert approved product intent into an executable, reviewable engineering contract and then into a minimal production scaffold. Keep product facts project-specific while reusing the common engineering system.

Version: **1.1**

## Operating modes

Choose one mode from the request and repository state:

1. **Generate**: create a new project from approved product/design inputs.
2. **Adopt**: add the standard rules and missing foundations to an existing repository without rewriting working code.
3. **Audit**: compare an existing repository against the standard and report gaps; do not modify unless requested.
4. **Refresh**: update a previously generated baseline through an explicit decision record and migration plan.

## Required workflow

### 1. Establish authority

Read the product design, PRD, architecture, design system, prototypes, API/data specs, and existing repository instructions. Record their authority order.

Stop and report a `BASELINE_GAP` when authoritative sources conflict in a way that changes product behavior, permissions, money, privacy, data ownership, AI boundaries, or release scope. Do not silently choose.

For a new project, read [product-handoff.md](references/product-handoff.md) and create a completed product-to-engineering brief before scaffolding. For an existing project, inspect the worktree and preserve unrelated changes.

Read [requirement-change-system.md](references/requirement-change-system.md) whenever adding, changing, optimizing, deprecating, or removing product behavior. Assign a requirement ID before implementation and keep its traceability record current.

### 2. Build the project profile

Read [project-profile.md](references/project-profile.md). Create `.project/standard-project.json` from `assets/project-profile.example.json`.

Classify every choice as:

- `locked`: required by approved product or infrastructure constraints.
- `default`: inherited from this standard with no contrary requirement.
- `deferred`: intentionally postponed with a decision trigger.
- `forbidden`: excluded for the current phase.

Never infer business constants, roles, prices, thresholds, retention periods, content authority, or AI publication rights from the template.

### 3. Select the smallest sufficient architecture

Read [architecture-and-stack.md](references/architecture-and-stack.md).

Default to a modular monolith:

- pnpm workspace + Turborepo;
- Next.js App Router + React + TypeScript + Tailwind CSS + shadcn/ui;
- NestJS REST `/api/v1`;
- PostgreSQL + Prisma;
- S3-compatible object storage when binary assets exist;
- a separate Worker process only when background work exists.

Add Redis, SQS, an admin app, search infrastructure, or a dedicated SDK only when the profile satisfies the documented trigger. Do not introduce microservices, Kafka, Kubernetes, GraphQL, or distributed sagas without an approved ADR.

Pin exact runtime and dependency versions in the lockfile and baseline record. When the user requests current/latest versions, verify them from official primary sources before selecting them. Never use an unreviewed floating `latest` as CI input.

### 4. Generate the foundation

For a new project:

1. Copy `assets/project-profile.example.json` and complete it.
2. Run:

   ```text
   python scripts/scaffold_project.py --config <profile.json> --output <target-directory>
   ```

3. Install dependencies, create the lockfile, normalize generated files, and prove the foundation:

   ```text
   pnpm install
   pnpm format
   pnpm quality
   ```

4. Refine the generated repository in place; do not create parallel “formal” or “next” apps to avoid migration.
5. Replace every `BASELINE_GAP` and project placeholder that can be resolved from approved inputs.

The scaffold is a foundation, not evidence that product behavior is implemented. Read [generation-contract.md](references/generation-contract.md) for the required outputs and repository layout.

For adoption mode, map the existing layout to the target boundaries and apply surgical changes. Do not copy the scaffold over an occupied repository.

### 5. Install canonical rules

Read and apply:

- [engineering-rules.md](references/engineering-rules.md) for code, data, security, UI, Git, and documentation rules.
- [ai-rules.md](references/ai-rules.md) for development AI and product AI boundaries.
- [quality-gates.md](references/quality-gates.md) for tests, CI, security, accessibility, and release evidence.
- [multi-agent-system.md](references/multi-agent-system.md) for canonical rule discovery across Codex, Claude, Gemini, Copilot, and Cursor.
- [ai-review-system.md](references/ai-review-system.md) for the mandatory independent AI review gate.
- [deployment-system.md](references/deployment-system.md) for local containers, release images, migrations, health checks, smoke tests, and recovery.

Create one root `AGENTS.md` as the canonical repository instruction source. Tool-specific files may only point to it and must not duplicate or redefine business rules.

Keep product invariants in the generated repository's approved product baseline, not in this reusable skill.

### 6. Implement by traced vertical slice

Implement one end-to-end user or operator loop before horizontally expanding features:

```text
UI states → API contract → application/domain rule → persistence
→ async work/provider boundary → audit/observability → tests
```

Update code, contract, migration, documentation, and tests in the same coherent change whenever behavior changes.

Every change must map:

```text
REQ/OPT ID → acceptance criteria → affected contracts/modules
→ implementation → tests → AI review → release evidence
```

### 7. Run mandatory AI review

After implementation and automated checks, require an AI reviewer to inspect the authoritative requirements and raw diff. Prefer a separate agent or fresh review context that did not implement the change.

The review must produce a schema-valid report under `artifacts/ai-review/` and cover product drift, architecture boundaries, contracts, data/migrations, authorization/privacy, AI governance, tests, observability, and deployment.

- Block handoff on unresolved `blocker` or `high` findings.
- Resolve findings in code or record an approved, expiring exception with evidence.
- Re-run affected checks and AI review after fixes.
- Keep human review optional and non-blocking for ordinary VibeCoding changes. Invite it when available; require it only when an external law, organizational policy, or explicit user instruction demands it.

Do not let the implementing AI self-approve in the same reasoning pass when an independent agent or fresh context is available.

### 8. Verify, package, and hand off

Run the smallest relevant checks first, then the applicable aggregate gate. Never weaken, skip, or fabricate a check to obtain a green result.

Before deployment:

- run `quality:full`;
- create approved visual snapshot baselines with Playwright on the same platform used by CI, commit them, then prove `test:visual` fails on drift and passes unchanged;
- validate the AI review report;
- build immutable container images;
- apply migrations through the generated deployment procedure;
- verify health/readiness and smoke tests;
- retain rollback or forward-recovery instructions.

Deliver:

- outcome and generated/adopted mode;
- profile and ADR decisions;
- files and behavior changed;
- migrations, configuration, and secrets required;
- exact checks run and results;
- checks not run and why;
- AI reviewer identity/context, report path, findings, and resolutions;
- known `BASELINE_GAP` items and risks;
- deployment target, image/version, migration, smoke, and recovery evidence;
- next safe action.

For a reusable standalone prompt instead of Skill invocation, use [bootstrap-prompt.md](references/bootstrap-prompt.md).

## Non-negotiable behavior

- Prefer stability, reuse, schema-first/API-first work, minimal coherent diffs, and reversible decisions.
- Preserve user changes and never perform destructive Git operations without explicit authorization.
- Keep browser code away from databases, private infrastructure SDKs, provider secrets, and server-only configuration.
- Keep controllers thin and domain rules independent of frameworks and persistence.
- Treat PostgreSQL as business truth; treat Redis and queues as derived or delivery infrastructure.
- Validate all boundary input at runtime; never expose Prisma models as public contracts or UI props.
- Represent money and ratios as integers; use append-only corrections for financial, audit, score, and published records when those domains exist.
- Model explicit loading, empty, error, permission, processing, success, focus, disabled, and destructive UI states.
- Require internationalization, accessibility, weak-network behavior, privacy, provenance, moderation, and observability when relevant to the product.
- Treat AI output as an untrusted candidate. Require provenance, review, lifecycle, fallback, and explicit authorization before publication or training.
- Require an independent AI review artifact for every material code or behavior change. Human review is encouraged but not a default blocking gate.
- Keep requirements, acceptance criteria, implementation, tests, review, and release evidence traceable by stable IDs.
- Do not claim deployability without container/release assets, health checks, migrations, smoke tests, and recovery evidence.
- Report evidence honestly. “Code written” is not equivalent to “feature accepted” or “production ready.”
