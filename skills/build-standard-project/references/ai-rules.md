# AI rules

## Development AI

Root `AGENTS.md` owns project execution and continuation rules. Use the Skill entrypoint for routing/defaults; do not maintain another copy of Routine here. Read [quality-checks.md](quality-checks.md) for affected validation boundaries and [product-change-notes.md](product-change-notes.md) for change/test evidence details.

## Product AI

Treat generated output as untrusted input. Before enabling an AI capability, define:

- allowed inputs and prohibited/private data;
- provider/model boundary, timeout, cost limit, and fallback;
- how users can distinguish, review, reject, or remove generated content;
- provenance, publication, consent, retention, and incident handling where relevant.

Provider failure is never a successful domain outcome. Do not fabricate citations, authority, rights, identity, or confidence. Do not automatically publish generated content or use private content for training without explicit authorization and an approved data boundary.

Add versioning, hashes, multi-stage lifecycles, moderation queues, or detailed audit records only when the product or compliance requirement needs them.
