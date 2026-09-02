# AI rules

## Development AI

- Read root `AGENTS.md`, repository state, and only the product/engineering sources relevant to the task.
- Do safe in-scope local work without repeated confirmation. Ask once only when a missing decision materially changes behavior, architecture, cost, or risk.
- Make the smallest coherent change, preserve user work, and reuse existing code and conventions.
- Record every requirement change, optimization, bug fix, or behavior-affecting maintenance change in the repository's single change record.
- Update directly affected contracts, migrations, docs, and tests; every bug fix needs a regression test.
- Review the final diff, run proportionate checks, and report results honestly.
- Do not expose secrets/private data, invent product rules, use destructive operations, add speculative infrastructure, or perform external writes without authorization.
- Do not narrate internal deliberation, reopen settled decisions without new evidence, or rerun unaffected checks.

Routine work needs only the existing concise change record and affected test, not a parallel requirement ledger, review file, or evidence package. For release or an affected high-risk boundary, use the repository's existing product/issue source and request a focused independent review when it adds real assurance.

## Product AI

Treat generated output as untrusted input. Before enabling an AI capability, define:

- allowed inputs and prohibited/private data;
- provider/model boundary, timeout, cost limit, and fallback;
- how users can distinguish, review, reject, or remove generated content;
- provenance, publication, consent, retention, and incident handling where relevant.

Provider failure is never a successful domain outcome. Do not fabricate citations, authority, rights, identity, or confidence. Do not automatically publish generated content or use private content for training without explicit authorization and an approved data boundary.

Add versioning, hashes, multi-stage lifecycles, moderation queues, or detailed audit records only when the product or compliance requirement needs them.
