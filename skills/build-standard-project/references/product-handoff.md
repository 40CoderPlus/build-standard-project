# Product-to-engineering handoff

Use this contract before creating project code.

## Required inputs

Capture:

1. Product name, one-line positioning, target users, primary jobs, and non-goals.
2. Release phase and in/out-of-scope capabilities.
3. User and operator loops with success, failure, cancellation, retry, and recovery.
4. Roles, ownership, entitlements, task grants, moderation, and audit requirements.
5. Domain entities, lifecycle states, invariants, history, deletion, and retention.
6. Public/private data, PII, secrets, payment, location, content-rights, and consent boundaries.
7. External providers, availability assumptions, cost limits, timeouts, and fallbacks.
8. AI capabilities, prohibited uses, training consent, provenance, review, and publication rules.
9. Supported locales, source copy, accessibility target, viewports, weak-network and offline behavior.
10. Design-system tokens, approved high-fidelity screens, interaction prototype, and responsive rules.
11. Product metrics and analytics governance.
12. Expected users/traffic, latency/availability objectives, growth uncertainty, budget, deadline, team skills, deployment target, compliance, recovery, and operational ownership.
13. Existing organizational review or compliance policies that materially constrain delivery.

Before scaffolding, normally present the minimum sufficient option and at most one justified upgrade, then obtain one user decision. Show a complex third option only when approved requirements already require it. Infer from approved inputs first and batch only architecture-changing gaps. Missing forecasts may remain ranges; missing user approval may not be treated as a default architecture decision.

## Authority order

Create an explicit order such as:

```text
approved product/contract baseline
→ approved architecture/API/data baseline
→ design tokens
→ high-fidelity screens
→ interaction prototype
→ research/history
→ chat and temporary notes
```

Machine-executable artifacts win only inside their declared domain:

- merged migrations and schema are the database fact;
- generated and CI-verified OpenAPI is the API fact;
- runtime tokens are the UI-token fact;
- the lockfile is the resolved dependency fact.

If they contradict approved intent, record and fix the contradiction; do not silently redefine the product.

## Feature classification

For each feature, record:

- existing issue or feature reference when available;
- product/module owner;
- primary user and job;
- phase: now, next, later, or out of scope;
- entities and state transitions;
- authorization and audit;
- trust: source, rights, provenance, review, expiry, moderation;
- privacy and retention;
- locale and accessibility;
- meaningful outcome metric;
- dependencies and fallback;
- UI, API, data, job, event, and test landing points.
- deployment and recovery evidence when the feature affects them.

When authoritative inputs conflict, report the sources, behavioral/security impact, options, decision owner, and blocked scope in plain language. Do not use placeholders on a critical path when the approved inputs already contain the answer.
