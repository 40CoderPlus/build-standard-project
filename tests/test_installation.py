import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "build-standard-project"


class InstallationTest(unittest.TestCase):
    def run_installer(self, roots: list[Path]) -> None:
        if os.name == "nt":
            shell = shutil.which("pwsh") or shutil.which("powershell")
            if not shell:
                self.skipTest("PowerShell is unavailable")
            command = [
                shell, "-NoProfile", "-File", str(ROOT / "install.ps1"),
                "-InstallRoot", str(roots[0]), "-ClaudeRoot", str(roots[1]),
                "-AgentsRoot", str(roots[2]),
            ]
            environment = os.environ.copy()
        else:
            shell = shutil.which("sh")
            if not shell:
                self.skipTest("POSIX shell is unavailable")
            command = [shell, str(ROOT / "install.sh")]
            environment = {
                **os.environ,
                "CODEX_HOME": str(roots[0]),
                "CLAUDE_CONFIG_DIR": str(roots[1]),
                "AGENTS_HOME": str(roots[2]),
            }
        result = subprocess.run(
            command, env=environment, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_three_hosts_preserve_independent_skills_and_backup_outside_discovery(self):
        with tempfile.TemporaryDirectory(prefix="bsp-install-") as temporary:
            roots = [Path(temporary) / name for name in ("codex", "claude", "agents")]
            for root in roots:
                neighbor = root / "skills" / "independent-design"
                neighbor.mkdir(parents=True)
                (neighbor / "SKILL.md").write_text("keep my independent skill", encoding="utf-8")
            self.run_installer(roots)
            for root in roots:
                target = root / "skills" / "build-standard-project"
                self.assertEqual((target / "SKILL.md").read_bytes(), (SOURCE / "SKILL.md").read_bytes())
                self.assertTrue((target / "references" / "ui-workflow.md").is_file())
                (target / "local-note.txt").write_text("preserve on upgrade", encoding="utf-8")
            self.run_installer(roots)
            for root in roots:
                target = root / "skills" / "build-standard-project"
                self.assertFalse((target / "local-note.txt").exists())
                self.assertEqual(
                    sorted(path.name for path in (root / "skills").iterdir()),
                    ["build-standard-project", "independent-design"],
                )
                backups = list((root / "skill-backups").iterdir())
                self.assertEqual(len(backups), 1)
                self.assertEqual((backups[0] / "local-note.txt").read_text(), "preserve on upgrade")
                self.assertEqual(
                    (root / "skills" / "independent-design" / "SKILL.md").read_text(),
                    "keep my independent skill",
                )

    def test_shared_host_roots_are_installed_only_once(self):
        with tempfile.TemporaryDirectory(prefix="bsp-shared-") as temporary:
            shared = Path(temporary) / "shared"
            self.run_installer([shared] * 3)
            self.assertFalse((shared / "skill-backups").exists())
            self.assertEqual(len(list((shared / "skills").iterdir())), 1)


if __name__ == "__main__":
    unittest.main()
