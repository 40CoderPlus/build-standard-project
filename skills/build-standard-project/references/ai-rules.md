# AI rules

## Development AI

Before changing a repository:

1. Read root `AGENTS.md`, approved product baseline, and task-relevant architecture/API/data/design/quality documents.
2. Inspect existing implementation and repository state.
3. Identify affected contracts, domains, pages, migrations, providers, security controls, and tests.
4. State unresolved assumptions; create `BASELINE_GAP` for authoritative conflicts.
5. Plan the smallest coherent and reversible change.

Development AI must:

- reuse existing code, tokens, schemas, providers, clocks, IDs, and fixtures;
- protect unrelated and user-authored work;
- synchronize behavior changes with contracts, documentation, migrations, and tests;
- validate before claiming completion;
- report exact commands, results, skipped checks, and remaining risk;
- keep production writes, deployments, messages, permission changes, and other external effects inside explicit user authorization.
- leave a traceable requirement record and request an independent AI review before acceptance.

Development AI must not:

- read, reveal, copy, or commit real secrets or unnecessary production/user data;
- invent business rules, roles, constants, rights, sources, consent, approval, or completion status;
- use destructive Git/filesystem operations or rewrite history without explicit authorization;
- bypass migrations, tests, security, accessibility, moderation, or quality thresholds;
- delete or weaken checks to make CI pass;
- create placeholder success, silent fallback, false PASS, or TODO logic on a release-critical path;
- expose persistence/provider types as public contracts;
- silently introduce dependencies, global state, microservices, or new infrastructure.
- approve its own material change in the same reasoning pass when a separate reviewer or fresh context is available.

## AI review

- Treat the implementing agent and reviewing agent as separate roles.
- Give the reviewer authoritative requirements, raw diff, affected files, and test evidence.
- Do not leak expected findings or the implementer's preferred conclusion.
- Block acceptance and deployment on unresolved blocker/high findings.
- Re-run affected checks and review after fixes.
- Keep human review optional for ordinary VibeCoding; AI review remains mandatory.

## Product AI

Treat every generated result as an untrusted candidate.

For each AI capability, define:

- allowed inputs and prohibited data;
- provider adapter and approved model class;
- model/version availability;
- prompt/parameter version;
- normalized input and output hashes;
- cost, latency, timeout, retry, and fallback;
- output nature label;
- provenance and source limitations;
- automated validation;
- human review and named accountability;
- lifecycle: requested → queued → generated → scanned/validated → pending review → approved/rejected → published/frozen/archived;
- audit, metrics, incident response, deletion, and withdrawal.

Hard defaults:

- Provider timeout/error is not approval or PASS.
- AI output is not a cultural, scholarly, legal, safety, financial, or moderation authority.
- AI content is not automatically published.
- Do not fabricate citations, experts, rights, licenses, identity, confidence, or model versions.
- Keep AI-generated, human-created, reconstructed, translated, and editorial content visibly distinguishable where the distinction matters.
- Separate display/publication consent from model-training consent. Missing consent means no training.
- Do not send private content or PII to a general external model without an approved data-processing boundary.
- A successful experiment does not silently change the product contract.

Require explicit approval and baseline changes before adding a provider/model category, expanding data use, enabling training, permitting automatic publication, or weakening a prohibited-use boundary.
