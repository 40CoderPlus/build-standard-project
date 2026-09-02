# Change record

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
