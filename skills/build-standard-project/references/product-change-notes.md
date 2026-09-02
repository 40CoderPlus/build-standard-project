# Product change notes

Record every requirement change, optimization, and bug fix. Generated projects keep one append-only, human-readable record at `docs/changes.md`; an existing repository may use its established changelog, issue, or pull request instead.

Do not introduce a parallel ledger, custom lifecycle, stable-ID scheme, or cryptographic binding. The record exists to preserve intent and test evidence, not to reproduce project management inside the repository.

## Minimum useful record

Each entry captures only:

- type: `requirement`, `optimization`, `bug`, or `maintenance`;
- the observable change and its reason;
- directly affected test file paths;
- an existing issue or pull-request link when one exists.

Requirement changes and optimizations need a directly affected test when source behavior changes. Every bug fix needs a regression test that fails for the reported behavior before the fix and passes afterward. If a request changes only product documentation and no executable behavior, the record is still required but a new test is not.

Require explicit user or product-owner direction when the change alters positioning, money, legal/privacy duties, irreversible data semantics, external authority, product-AI prohibited uses, or another locked invariant.

## Workflow

1. Reuse the existing source of truth and resolve material conflicts.
2. Add the concise change entry and identify the affected test.
3. Implement the smallest coherent vertical slice.
4. Update directly affected contracts, migrations, docs, and tests with the code.
5. Run the regression/affected test and proportionate checks.
6. For release or high-risk work, request the focused independent review described in [independent-review.md](independent-review.md).

The bundled generator adds one lightweight CI check: behavior-affecting source changes must modify `docs/changes.md`, modify at least one test, and cite that changed test in the new entry. It does not map every file, hash diffs, or infer whether the written explanation is truthful; final-diff review still owns semantic correctness.
