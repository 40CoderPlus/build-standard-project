import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATOR = ROOT / "skills" / "build-standard-project" / "scripts" / "migrate_legacy_project.py"


LEGACY_AGENTS = """# Legacy Product repository instructions

This is the canonical instruction source for humans and AI coding tools.

- Assign a stable REQ/OPT ID before changing behavior.
- Require an independent AI review report for every material change.

## Completion

Run the smallest relevant checks followed by `pnpm quality:full`.
"""

LEGACY_WORKFLOW = """name: Quality

on:
  pull_request:
  push:

permissions:
  contents: read

env:
  DATABASE_URL: postgresql://example
  AI_REVIEW_BASE_SHA: ${{ github.event.pull_request.base.sha || github.event.before }}

concurrency:
  group: quality-${{ github.ref }}

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: pnpm/action-setup@v4
      - run: pnpm quality

  full:
    needs: quality
    runs-on: ubuntu-latest
    steps:
      - run: pnpm security:sbom:generate
      - run: pnpm quality:full
"""


class LegacyUpgradeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary.name)
        (self.project / ".github" / "workflows").mkdir(parents=True)
        (self.project / "AGENTS.md").write_text(LEGACY_AGENTS, encoding="utf-8")
        (self.project / ".github" / "workflows" / "quality.yml").write_text(
            LEGACY_WORKFLOW, encoding="utf-8"
        )
        package = {
            "name": "legacy-product",
            "scripts": {
                "format:check": "prettier --check .",
                "lint": "eslint .",
                "typecheck": "tsc --noEmit",
                "test": "vitest run --coverage",
                "contract:check": "turbo run contract:check",
                "migration:check": "node scripts/quality/check-migrations.mjs",
                "build": "turbo run build",
                "validate:requirements": "node scripts/quality/check-requirements.mjs",
                "review:ai:check": "node scripts/quality/check-ai-review.mjs",
                "review:fingerprint": "node scripts/quality/review-fingerprint.mjs",
                "security:secrets": "node scripts/quality/check-secrets.mjs",
                "quality": "pnpm format:check && pnpm test && pnpm validate:requirements && pnpm review:ai:check",
                "quality:full": "pnpm quality && pnpm review:fingerprint && pnpm security:secrets",
            },
        }
        (self.project / "package.json").write_text(json.dumps(package), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_migrator(self, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(MIGRATOR), "--project", str(self.project), *arguments],
            check=False,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )

    def test_dry_run_then_apply_removes_legacy_routine_work(self) -> None:
        before = (self.project / "package.json").read_text(encoding="utf-8")
        plan = self.run_migrator()
        self.assertEqual(plan.returncode, 0, plan.stderr)
        self.assertIn("[PLAN]", plan.stdout)
        self.assertEqual((self.project / "package.json").read_text(encoding="utf-8"), before)

        applied = self.run_migrator("--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        package = json.loads((self.project / "package.json").read_text(encoding="utf-8"))
        scripts = package["scripts"]
        self.assertEqual(scripts["test"], "vitest run")
        self.assertEqual(scripts["quality:fast"], "pnpm test")
        self.assertEqual(scripts["change:check"], "node scripts/quality/check-change-record.mjs")
        self.assertNotIn("validate:requirements", scripts)
        self.assertNotIn("review:ai:check", scripts)
        self.assertNotIn("review:fingerprint", scripts)
        self.assertNotIn("security:secrets", scripts)
        self.assertNotIn("validate:requirements", scripts["quality"])
        self.assertNotIn("review:fingerprint", scripts["quality:full"])

        agents = (self.project / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("pnpm test -- path/to/affected.test.ts", agents)
        self.assertIn("Do not run `pnpm quality`, `pnpm quality:full`", agents)
        self.assertNotIn("stable REQ/OPT ID", agents)

        workflow = (self.project / ".github" / "workflows" / "quality.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("workflow_dispatch:", workflow)
        self.assertIn("run: pnpm change:check", workflow)
        self.assertIn("run: pnpm quality:fast", workflow)
        self.assertIn("if: github.event_name == 'workflow_dispatch'", workflow)
        self.assertNotIn("      - run: pnpm quality\n", workflow)
        self.assertNotIn("AI_REVIEW_BASE_SHA", workflow)
        self.assertNotIn("security:sbom:generate", workflow)
        self.assertTrue((self.project / "docs" / "changes.md").is_file())
        self.assertTrue(
            (self.project / "scripts" / "quality" / "check-change-record.mjs").is_file()
        )

        repeated = self.run_migrator()
        self.assertEqual(repeated.returncode, 0, repeated.stderr)
        self.assertIn("No generated v1.1-v1.6", repeated.stdout)

    def test_refuses_unrecognized_agents_file(self) -> None:
        custom = "# Custom rules\n\nAlways run the project-specific checks.\n"
        (self.project / "AGENTS.md").write_text(custom, encoding="utf-8")

        result = self.run_migrator("--apply")

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not a recognized generated template", result.stderr)
        self.assertEqual((self.project / "AGENTS.md").read_text(encoding="utf-8"), custom)

    def test_recognizes_generated_v1_6_agents(self) -> None:
        generated_v1_6 = """# Legacy Product repository instructions

This is the canonical instruction source.

## Validate

- Routine: use the fast path. No REQ/OPT, independent review artifact, aggregate gate, E2E/visual suite, or deployment evidence by default.
"""
        (self.project / "AGENTS.md").write_text(generated_v1_6, encoding="utf-8")

        result = self.run_migrator("--apply")

        self.assertEqual(result.returncode, 0, result.stderr)
        migrated = (self.project / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("pnpm test -- path/to/affected.test.ts", migrated)


if __name__ == "__main__":
    unittest.main()
