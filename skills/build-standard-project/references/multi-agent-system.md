# Multi-agent rule system

## One canonical source

Keep root `AGENTS.md` as the only canonical repository rule source. Generate tool adapters that only point to it:

```text
CLAUDE.md
GEMINI.md
.github/copilot-instructions.md
.cursor/rules/project.mdc
```

Do not duplicate product invariants, architecture, security, quality, or review rules in adapters.

## Adapter contract

Each adapter must say:

1. Read root `AGENTS.md` in full before analysis or edits.
2. Read the product baseline and task-relevant requirement.
3. Treat `AGENTS.md` as authoritative on conflict.
4. Do not create tool-specific alternative rules.

Run `pnpm validate:agent-rules` in CI to verify the adapters exist, point to `AGENTS.md`, and contain no copied rule sections.

## Agent execution protocol

Do not require multi-agent execution for routine changes. A single implementing agent may perform the focused final-diff review and relevant unit tests. Use the roles below only for initialization, release, high-risk/product-significant work, or an explicitly requested independent review.

Every implementing agent must:

- identify its role as implementer or reviewer;
- record the requirement ID when the selected route requires traceability;
- preserve repository state and user changes;
- state assumptions and `BASELINE_GAP` items;
- produce exact validation evidence;
- never approve its own material change in the same reasoning pass when an independent reviewer is available.

Every reviewing agent must:

- receive authoritative requirements and the raw diff, not the implementer's conclusions;
- inspect changed and affected files;
- verify tests and reported command evidence;
- emit the standard AI review report;
- avoid rewriting code unless explicitly asked to fix findings.

## Human participation

Human review is optional and non-blocking for normal VibeCoding. Do not configure mandatory approval counts by default.

Human input becomes blocking only when:

- the user explicitly requires it;
- external policy or law requires it;
- a locked product decision lacks authority;
- production credentials, irreversible data loss, financial release, or another high-impact external action needs new authorization.

Applicable automated checks remain blocking. Independent AI review is blocking only when the selected route requires it.
