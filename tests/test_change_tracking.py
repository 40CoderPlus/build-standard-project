import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "skills" / "build-standard-project" / "scripts" / "scaffold_project.py"


def approved_profile() -> dict:
    return {
        "schemaVersion": "1.4.0",
        "project": {
            "name": "validation-product",
            "displayName": "Validation Product",
            "packageScope": "validation",
            "description": "Validate the generated project.",
        },
        "product": {
            "phase": "MVP",
            "sourceOfTruth": "docs/product/README.md",
            "locales": ["en"],
            "defaultLocale": "en",
        },
        "architecture": {
            "selectionStatus": "approved",
            "selectionMode": "user-approved",
            "selectedOption": "modular-monolith",
            "consideredOptions": [
                {"id": "lean-managed", "fit": "Considered for validation."},
                {"id": "modular-monolith", "fit": "Approved for validation."},
            ],
        },
        "runtime": {"node": "24.18.0", "pnpm": "9.15.0", "typescript": "5.9.3"},
        "web": {
            "enabled": True,
            "next": "16.2.12",
            "react": "19.2.8",
            "tailwind": "4.3.3",
            "designSystem": "project tokens",
        },
        "api": {
            "enabled": True,
            "nest": "11.1.28",
            "adapter": "fastify",
            "basePath": "/api/v1",
        },
        "data": {"database": "postgresql", "databaseVersion": "18", "prisma": "7.9.0"},
        "apps": {"admin": False, "worker": False},
        "async": {"mode": "none", "redis": False},
        "storage": {"mode": "s3-compatible"},
        "auth": {"mode": "adapter-deferred"},
        "deployment": {
            "selectionStatus": "approved",
            "mode": "container-generic",
            "environments": ["development", "staging", "production"],
        },
        "quality": {
            "integration": "deferred",
            "e2e": "deferred",
            "crossBrowser": "deferred",
            "accessibility": "deferred",
            "visual": "deferred",
        },
        "decisions": [],
    }


class ChangeTrackingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.profile = self.base / "profile.json"
        self.output = self.base / "project"
        self.profile.write_text(json.dumps(approved_profile()), encoding="utf-8")
        subprocess.run(
            [sys.executable, str(GENERATOR), "--config", str(self.profile), "--output", str(self.output)],
            check=True,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_generator_connects_change_record_to_ci(self) -> None:
        package = json.loads((self.output / "package.json").read_text(encoding="utf-8"))
        workflow = (self.output / ".github" / "workflows" / "quality.yml").read_text(encoding="utf-8")

        self.assertEqual(
            package["scripts"]["change:check"],
            "node scripts/quality/check-change-record.mjs",
        )
        self.assertTrue((self.output / "docs" / "changes.md").is_file())
        self.assertIn("run: pnpm change:check", workflow)
        self.assertIn("run: pnpm quality:fast", workflow)
        agents = (self.output / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("pnpm test -- path/to/affected.test.ts", agents)
        self.assertIn("Do not run `pnpm quality`, `pnpm quality:full`", agents)

    @unittest.skipUnless(shutil.which("git") and shutil.which("node"), "requires git and node")
    def test_checker_accepts_explained_existing_coverage_only_for_non_bugs(self) -> None:
        def run(*command: str, check: bool = True) -> subprocess.CompletedProcess:
            return subprocess.run(
                command, cwd=self.output, check=check, capture_output=True,
                encoding="utf-8", errors="replace",
            )

        run("git", "init")
        run("git", "config", "user.email", "validation@example.invalid")
        run("git", "config", "user.name", "Validation")
        run("git", "add", ".")
        run("git", "commit", "-m", "baseline")
        source = self.output / "packages/domain/src/index.ts"
        source.write_text(source.read_text(encoding="utf-8") + "\n// Preserve invariant behavior.\n", encoding="utf-8")
        record = self.output / "docs/changes.md"
        baseline_record = record.read_text(encoding="utf-8")
        test_path = "packages/domain/test/invariant.test.ts"
        explanation = "existing coverage: invariant success and failure behavior is unchanged"

        cases = [
            ("optimization", f"`{test_path}` — {explanation}", True),
            ("maintenance", f"`{test_path}` — {explanation}", True),
            ("requirement", f"`{test_path}` — {explanation}", True),
            ("optimization", f"`{test_path}`", False),
            ("optimization", f"`{test_path}` — existing coverage:", False),
            ("optimization", f"`packages/domain/test/missing.test.ts` — {explanation}", False),
            ("optimization", f"`packages/domain/test` — {explanation}", False),
            ("optimization", f"`not applicable` — {explanation}", False),
            ("bug", f"`{test_path}` — {explanation}", False),
        ]
        for kind, evidence, accepted in cases:
            with self.subTest(kind=kind, evidence=evidence):
                record.write_text(
                    baseline_record + f"\n## 2026-09-06 — Preserve invariants\n\n"
                    f"- Type: {kind}\n- Change: Preserve existing behavior.\n- Tests: {evidence}\n",
                    encoding="utf-8",
                )
                result = run("node", "scripts/quality/check-change-record.mjs", "--base", "HEAD", check=False)
                self.assertEqual(result.returncode == 0, accepted, result.stderr)

        record.write_text(
            baseline_record + "\n## 2026-09-06 — Preserve invariants\n\n"
            f"- Type: optimization\n- Change: Preserve existing behavior.\n- Tests: `{test_path}` — {explanation}\n",
            encoding="utf-8",
        )
        (self.output / test_path).unlink()
        missing = run("node", "scripts/quality/check-change-record.mjs", "--base", "HEAD", check=False)
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("missing or untracked test", missing.stderr)

    @unittest.skipUnless(shutil.which("git") and shutil.which("node"), "requires git and node")
    def test_checker_requires_record_and_changed_regression_test(self) -> None:
        def run(*command: str, check: bool = True) -> subprocess.CompletedProcess:
            return subprocess.run(
                command,
                cwd=self.output,
                check=check,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
            )

        run("git", "init")
        run("git", "config", "user.email", "validation@example.invalid")
        run("git", "config", "user.name", "Validation")
        run("git", "add", ".")
        run("git", "commit", "-m", "baseline")

        source = self.output / "packages" / "domain" / "src" / "index.ts"
        source.write_text(source.read_text(encoding="utf-8") + "\nexport const invariantCode = 'INVALID';\n", encoding="utf-8")
        checker = ("node", "scripts/quality/check-change-record.mjs", "--base", "HEAD")

        missing_record = run(*checker, check=False)
        self.assertNotEqual(missing_record.returncode, 0)
        self.assertIn("Update docs/changes.md", missing_record.stderr)

        record = self.output / "docs" / "changes.md"
        record.write_text(
            record.read_text(encoding="utf-8")
            + """

## 2026-08-28 — Preserve the invariant code

- Type: bug
- Change: Export a stable invariant code for callers.
- Tests: `not applicable` — no regression test yet.
- Source: test fixture.
""",
            encoding="utf-8",
        )
        missing_regression = run(*checker, check=False)
        self.assertNotEqual(missing_regression.returncode, 0)
        self.assertIn("must cite its regression test", missing_regression.stderr)

        test_path = self.output / "packages" / "domain" / "test" / "invariant.test.ts"
        record.write_text(
            record.read_text(encoding="utf-8").replace(
                "`not applicable` — no regression test yet",
                "`packages/domain/test/invariant.test.ts` — regression for the exported code",
            ),
            encoding="utf-8",
        )
        unchanged_test = run(*checker, check=False)
        self.assertNotEqual(unchanged_test.returncode, 0)
        self.assertIn("must cite a test changed in this diff", unchanged_test.stderr)

        test_path.write_text(
            test_path.read_text(encoding="utf-8")
            + "\nit('exports the stable invariant code', async () => {\n"
            + "  const { invariantCode } = await import('../src/index.js');\n"
            + "  expect(invariantCode).toBe('INVALID');\n"
            + "});\n",
            encoding="utf-8",
        )
        complete = run(*checker, check=False)
        self.assertEqual(complete.returncode, 0, complete.stderr)
        self.assertIn("Change record passed", complete.stdout)


if __name__ == "__main__":
    unittest.main()
