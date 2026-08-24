# Requirement change system

Use this system for initialization baselines, new features, product-significant/high-risk behavior, deprecations/removals with compatibility impact, and release-tracked work. Routine bug fixes, small optimizations, UI adjustments, and refactors do not require a requirement record unless the user or repository explicitly asks for one.

## Canonical artifacts

```text
docs/requirements/
  README.md
  requirements.json
  REQ-000-template.md
  REQ-<number>-<slug>.md
```

`requirements.json` is the machine-readable traceability index. The Markdown file contains product reasoning and acceptance details.

## Required lifecycle

```text
proposed → clarified → approved → implementing → ai_review
→ accepted → released → verified
                    ↘ rejected | superseded | rolled_back
```

Human approval is not a default VibeCoding blocker. An AI agent may move a well-specified, in-scope requirement from `clarified` to `approved` when all authoritative inputs agree and the action remains within user authorization. Record `approvalMode: ai-derived-from-approved-baseline`.

Require explicit user/product-owner input when the change alters positioning, money, legal/privacy duties, irreversible data semantics, external authority, AI prohibited uses, or another locked invariant.

## Requirement record

Each record must include:

- stable `REQ-*` or `OPT-*` ID;
- title, type, status, phase, source, owner, and approval mode;
- problem, user/job, current behavior, intended behavior, and non-goals;
- acceptance criteria with stable `AC-*` IDs;
- affected UI, API, events, data, jobs, providers, permissions, analytics, and docs;
- migration, compatibility, rollout, fallback, and recovery;
- locale, accessibility, privacy, security, provenance, moderation, and AI implications;
- implementation files/modules;
- deleted file paths recorded separately from files that still exist;
- tests mapped to acceptance IDs;
- AI review report and finding resolutions;
- release version and post-release verification.

## Traced change workflow

1. Search for an existing requirement and extend or supersede it; do not create a parallel truth.
2. Classify impact: `patch`, `minor`, `major`, or `locked-decision`.
3. Update the requirement and traceability index before code.
4. Implement the smallest vertical slice.
5. Update contracts, migrations, docs, tests, and operational evidence in the same change.
6. Run `pnpm validate:requirements`.
7. Run independent AI review and attach the report when the selected route requires it.
8. Mark `accepted` only after criteria and gates pass.
9. Mark `released` and `verified` only with deployment and smoke evidence.

Use `affected.files` for paths that exist in the reviewed head and `affected.deletedFiles` for deleted paths. A proposed, clarified, rejected, superseded, or merely approved record does not authorize code changes: only `implementing`, `ai_review`, `accepted`, `released`, or `verified` requirements may satisfy changed-file traceability.

CI must reject duplicate IDs, unknown statuses, missing acceptance mappings, nonexistent current file/test/review references, and accepted requirements with unresolved blocker/high findings. When `AI_REVIEW_BASE_SHA` is available, every material Git-diff file—including deletions—must belong to an implementing/reviewed/accepted/released/verified REQ or OPT. The referenced AI report must match the requirement ID, acceptance IDs, affected and deleted files, verdict, current content fingerprint, reviewed base/head SHAs, and exact binary Git-diff hash.
