# Change record

## 2026-09-06 — 2.0.0: Proportionate validation and model-neutral workflows

- Type: optimization
- Change: Clarify rule ownership and remove the duplicate Development AI workflow. Non-bug source changes may cite existing tracked tests with an `existing coverage:` explanation; bug fixes still require a changed regression test, and all cited tests must exist. Synchronize generated rules and references, allow focused UI verification when narrower checks are insufficient, preserve accepted constraints during mid-task corrections, and add an opt-in representative-task evaluation method. Update the package version and both READMEs; existing installations and generated projects are not automatically migrated.
- Tests: `tests/test_change_tracking.py` (3 tests, including 9 existing-coverage subcases and deleted-test rejection) and `tests/test_legacy_upgrade.py` (3 tests) passed. Skill quick validation could not run because the bundled Python lacks PyYAML; frontmatter, local reference links, and version consistency were checked directly instead. Cross-model task evaluation has not been run.
- Source: Direct request to implement the reviewed engineering improvements after the GPT-6 Astra upgrade.

## 2026-09-03 — Normalize current-project conversation titles

- Type: feature
- Change: Add an explicit metadata-only route for renaming current-project conversations as `MMDD｜TYPE｜Topic`, using `createdAt` in `Asia/Shanghai`, one run-wide TYPE vocabulary, evidence-based topics, and title-only mutation. Installers now also deploy the Skill to Claude Code's `~/.claude/skills` or `CLAUDE_CONFIG_DIR` location in addition to Codex and shared Agent directories.
- Tests: manual package validation passed for Skill frontmatter, PowerShell syntax, shell syntax, version consistency, and `git diff --check`. The bundled `quick_validate.py` could not run because its Python environment does not include PyYAML.
- Source: direct request and supplied naming prompt/screenshot.

## 2026-09-03 — Add fast commit-time quality gates

- Type: requirement
- Change: Initialization now records a non-configurable engineering-quality baseline in the project profile and architecture documentation. Generated and explicitly migrated projects install repository-local Git hooks that check formatting and lint only for relevant staged files, enforce Conventional Commit subjects, and establish change/test/regression expectations from the foundation. Full type, test, build, and browser suites remain outside the commit path.
- Tests: not run — the initialization-quality baseline update was requested without a test run.
- Source: direct request for basic quality checks at commit time.

## 2026-09-03 — Install for Codex and compatible agents

- Type: bug
- Change: Repository installers now place the Skill in both the Codex skills directory and the shared `~/.agents/skills` directory, with independent upgrade backups.
- Tests: not run — installer behavior change was requested without a test run.
- Source: direct report that Anthropic-compatible agents did not receive the installation.

## 2026-08-29 — Stop legacy projects from running Full for small Bugs

- Type: bug
- Change: Add an explicit v1.1-v1.6 project migration that replaces legacy generated Routine rules, coverage, requirement validation, fingerprints, AI Review, and always-on Full CI with a direct affected-test path. Installing the Skill alone is now clearly distinguished from migrating project-local rules.
- Tests: `tests/test_legacy_upgrade.py` — covers dry-run safety, known-template migration, fast CI conversion, idempotence, and refusal to overwrite custom Agent rules.
- Source: direct report that a small Bug still takes more than 20 minutes after upgrading.

## 2026-08-28 — Add lightweight change and regression protection

- Type: requirement
- Change: Generated projects keep one concise change record, require a directly affected changed test for behavior-source changes, require Bug entries to cite regression tests, and verify the linkage in pull-request CI.
- Tests: `tests/test_change_tracking.py` — covers missing records, missing Bug regression citations, unchanged cited tests, and the passing complete path.
- Source: direct request.
