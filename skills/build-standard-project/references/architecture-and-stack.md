# Architecture selection

Choose from product evidence, not template completeness.

## Inputs

Use approved materials to infer phase, domain complexity, users/traffic, data risk, latency/availability, background/realtime/search/media needs, budget, team/operations, compliance, recovery, and hosting constraints. Use ranges when uncertain; batch only decision-changing gaps once.

## Options

Present two options by default:

- **Minimum sufficient (recommended):** one deployable application and managed services where practical. No separate API, worker, queue, Redis, containers, monorepo, or orchestration unless required.
- **Next justified:** a modular application/API and only the extra data/async/deployment components supported by real requirements.

Present a **complex/high-assurance** third option only when requirements already demand independent scaling/isolation, regional or availability guarantees, heavy async/realtime/search, or genuine multi-team ownership. Complexity is not a future-proofing default.

Compare only: product fit, topology, deployment, delivery speed, operating cost, main limit/risk, and upgrade trigger. Recommend the minimum option that meets approved requirements.

## User choice and ownership

Before scaffolding, obtain one explicit choice covering topology, data/storage, optional async/realtime/search, and deployment. Do not implement a complex option or component without explicit selection.

After material costs, limits, and risks are stated, the user owns the chosen product/architecture/operations tradeoff. AI remains responsible for truthful disclosure and correct implementation; user ownership does not permit hidden known risk, fabricated evidence, or safety/legal bypasses.

If the user says “you decide,” choose the minimum sufficient option and record `user-delegated`. Otherwise record `user-approved`. Do not reopen the decision without new evidence.

## Complexity triggers

- Separate API: multiple clients, public/integration contract, independent backend boundary, or real team ownership.
- Worker/queue: work exceeds request limits or needs durable retry/delivery/burst handling.
- Redis/cache: measured latency/load, rate limit, or short-lock need; never business truth.
- Search engine: relational/full-text search cannot meet proven relevance, language, scale, or latency needs.
- Microservices/orchestration/multi-region: explicit isolation, independent scaling/ownership, availability, latency, residency, or recovery objectives justify their operating cost.

Across stacks, keep secrets and private infrastructure out of browsers, validate external input, use stable contracts and migrations, and make authorization, idempotency, audit, and recovery proportional to risk.
