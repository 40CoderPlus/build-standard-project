# Project profile

Create `.project/standard-project.json` as the machine-readable record of product-fit technology decisions. Start from `assets/project-profile.example.json`, whose technology values are illustrative candidates and remain inactive while `architecture.selectionStatus` is pending.

## Required fields

- `schemaVersion`
- `project.name`, `displayName`, `packageScope`, `description`
- `product.phase`, `sourceOfTruth`, `locales`, `defaultLocale`
- `architecture.selectionStatus`, `selectionMode`, `selectedOption`, `consideredOptions`
- selected runtime/language/framework/package-manager versions for enabled components
- enabled application/deployable units and their boundaries
- primary data, storage, authentication, async, realtime, search, and analytics choices when applicable
- `deployment.selectionStatus`, `mode`, `environments`
- `quality`
- `decisions`

The bundled modular-monolith generator additionally requires the existing `runtime`, `web`, `api`, `data`, `apps`, `async`, `storage`, and `auth` fields shown in the example. Other approved architectures may use a different profile shape under those sections; do not add irrelevant fields merely to resemble the example.

`quality` records both the non-configurable engineering baseline and optional suites. The baseline requires staged-file format/lint hooks, Conventional Commit subjects, one change record, directly affected tests, and Bug regression tests; the generator fills these values for compatible older profiles and rejects attempts to disable them. Keep optional `integration`, `e2e`, `crossBrowser`, `accessibility`, and `visual` suites `deferred` until the approved product slice needs them. Types, contracts, migration structure, and build remain standard commands outside the commit hook.

## Selection policy

Before finalizing the profile, use [architecture-and-stack.md](architecture-and-stack.md) to present product-fit options and obtain the user's choice. Record:

- each considered option and why it fits or fails;
- the recommended option and reasoning;
- the user's selected option, or explicit delegation to Codex;
- expected delivery/operating cost, major risks, and revisit triggers;
- the deployment target/provider if known, otherwise a deliberately deferred decision.

`selectionStatus` must remain `pending-user-choice` until the user decides. Use `selectionMode: user-approved` for a direct choice and `selectionMode: user-delegated` only when the user explicitly delegates. Do not convert silence into approval.

Use exact versions. Treat the bundled example as a tested baseline snapshot, not an eternal “latest” claim.

Component choices after approval:

- When the selected option needs a general relational business store, PostgreSQL is a strong candidate; compare hosting, migration, team, workload, and organizational constraints before final selection.
- When the user selects NestJS, Fastify is a strong adapter candidate unless an integration has a documented Express dependency.
- Default `apps.worker` to false. Enable PostgreSQL Job + Worker only when an approved requirement defines a real handler, lifecycle, retry/replay, lease/dead-letter, and health contract; never deploy an empty keepalive worker.
- Transactional Outbox + SQS when external delivery, independent scaling, or durable cross-process events are already required.
- No Redis until caching, rate limiting, or short distributed locks are required.
- No dedicated admin app until operator surface, isolation, or deployment requirements justify it.
- Identity adapter boundary always; choose Better Auth only after session, provider, account-linking, and deployment requirements are known.
- S3-compatible storage only when the product owns binary assets.
- Choose managed/serverless, container-generic, orchestrated containers, or another deployment model according to the approved option. Do not generate container assets for a managed/serverless choice unless they serve a stated portability need.
- Keep review policy outside the architecture profile unless the organization already has an explicit policy. Routine VibeCoding uses final-diff review plus relevant tests; release or high-risk work may request a focused independent review.

## Decision records

Each `decisions` entry contains:

```json
{
  "id": "ADR-001",
  "status": "accepted",
      "classification": "user-selected",
  "decision": "Use a modular monolith",
  "reason": "The user selected this after comparing the lean, modular, and scaled options for the approved product envelope",
  "revisitWhen": "A measured workload or ownership boundary requires independent deployment"
}
```

Never hide a deferred decision in code comments. Put the trigger and owner in the profile or an ADR. Record rejected options briefly so later agents do not reopen the decision without new evidence.
