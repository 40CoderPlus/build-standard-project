#!/usr/bin/env python3
"""Migrate generated v1.1-v1.6 project controls to the Routine fast path."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSETS = SKILL_ROOT / "assets"
LEGACY_SCRIPTS = {
    "validate:requirements",
    "validate:agent-rules",
    "validate:no-skipped-critical-tests",
    "review:ai:check",
    "review:fingerprint",
    "security:secrets",
    "security:sast",
    "security:sbom",
    "security:sbom:generate",
}
BASELINE_SCRIPTS = [
    "format:check",
    "lint",
    "typecheck",
    "test",
    "contract:check",
    "migration:check",
    "build",
]
FULL_SCRIPTS = [
    "migration:drift",
    "test:integration",
    "test:browser:prepare",
    "test:e2e",
    "test:cross-browser",
    "test:a11y",
    "test:visual",
    "security:audit",
    "security:audit:toolchain",
    "deploy:preflight",
]
HOOK_PREPARE = "node scripts/quality/install-git-hooks.mjs"
COMMIT_SCRIPTS = {
    "commit:check": "node scripts/quality/check-staged.mjs",
    "commit:message": "node scripts/quality/check-commit-message.mjs",
}


def fail(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)
    raise SystemExit(1)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        fail(f"Cannot read {path}: {error}")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def is_legacy_agents(text: str) -> bool:
    return "Assign a stable REQ/OPT ID" in text or (
        "No REQ/OPT, independent review artifact" in text
        and "This is the canonical instruction source." in text
    )


def display_name(agents: str, package: dict[str, Any]) -> str:
    match = re.search(r"^# (.+?) repository instructions\s*$", agents, flags=re.MULTILINE)
    if match:
        return match.group(1)
    name = package.get("name")
    return name if isinstance(name, str) and name else "Project"


def migrate_package(package: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    scripts = package.get("scripts")
    if not isinstance(scripts, dict):
        fail("package.json must contain a scripts object")

    changes: list[str] = []
    removed = sorted(name for name in LEGACY_SCRIPTS if name in scripts)
    for name in removed:
        del scripts[name]
    if removed:
        changes.append("disable legacy requirement/review/fingerprint/security wrapper scripts")

    test = scripts.get("test")
    if isinstance(test, str) and test.strip() == "vitest run --coverage":
        scripts["test"] = "vitest run"
        changes.append("remove default all-suite coverage from routine unit tests")

    if scripts.get("quality:fast") != "pnpm test":
        scripts["quality:fast"] = "pnpm test"
        changes.append("restore the unit-only quality:fast command")

    baseline = [f"pnpm {name}" for name in BASELINE_SCRIPTS if name in scripts]
    baseline_command = " && ".join(baseline)
    current_quality = scripts.get("quality")
    legacy_quality = isinstance(current_quality, str) and any(
        name in current_quality for name in LEGACY_SCRIPTS
    )
    if baseline_command and (legacy_quality or not isinstance(current_quality, str)):
        scripts["quality"] = baseline_command
        changes.append("remove legacy governance checks from the standard quality command")

    full = ["pnpm quality"] + [f"pnpm {name}" for name in FULL_SCRIPTS if name in scripts]
    full_command = " && ".join(full)
    current_full = scripts.get("quality:full")
    legacy_full = isinstance(current_full, str) and any(
        name in current_full for name in LEGACY_SCRIPTS
    )
    if legacy_full:
        scripts["quality:full"] = full_command
        changes.append("keep Full checks only for release or affected high-risk work")

    if scripts.get("change:check") != "node scripts/quality/check-change-record.mjs":
        scripts["change:check"] = "node scripts/quality/check-change-record.mjs"
        changes.append("add the lightweight change/test linkage check")

    prepare = scripts.get("prepare")
    if isinstance(prepare, str) and prepare.strip():
        if HOOK_PREPARE not in prepare:
            scripts["prepare"] = f"{prepare} && {HOOK_PREPARE}"
            changes.append("install repository-local Git hooks after the existing prepare step")
    else:
        scripts["prepare"] = HOOK_PREPARE
        changes.append("install repository-local Git hooks during dependency setup")

    for name, command in COMMIT_SCRIPTS.items():
        if name not in scripts:
            scripts[name] = command
            changes.append(f"add the {name} commit-time quality command")

    return package, changes


def migrate_ci(text: str) -> tuple[str, list[str]]:
    if "name: Quality" not in text or "pnpm/action-setup" not in text:
        return text, []

    changes: list[str] = []
    updated = text.replace("\r\n", "\n")
    legacy_ci_lines = [
        "  AI_REVIEW_BASE_SHA: ${{ github.event.pull_request.base.sha || github.event.before }}\n",
        "      - run: pnpm security:sbom:generate\n",
    ]
    if any(line in updated for line in legacy_ci_lines):
        for line in legacy_ci_lines:
            updated = updated.replace(line, "")
        changes.append("remove unused AI Review and SBOM workflow hooks")
    if "  workflow_dispatch:\n" not in updated:
        updated = updated.replace("  push:\n", "  push:\n  workflow_dispatch:\n", 1)
        changes.append("make the Full CI job manually triggerable")

    if "CHANGE_BASE_SHA:" not in updated:
        env_line = "  CHANGE_BASE_SHA: ${{ github.event.pull_request.base.sha || github.event.before }}\n"
        marker = "\nconcurrency:"
        if "\nenv:\n" in updated and marker in updated:
            updated = updated.replace(marker, f"\n{env_line}{marker.lstrip()}", 1)
        elif marker in updated:
            updated = updated.replace(marker, f"\nenv:\n{env_line}\nconcurrency:", 1)
        else:
            updated = updated.replace("\njobs:\n", f"\nenv:\n{env_line}\njobs:\n", 1)
        changes.append("provide the CI base revision for change:check")

    if "      - run: pnpm quality\n" in updated:
        updated = updated.replace(
            "      - run: pnpm quality\n", "      - run: pnpm quality:fast\n", 1
        )
        changes.append("replace pull-request quality with the unit-only fast path")

    if "run: pnpm change:check" not in updated and "      - run: pnpm quality:fast\n" in updated:
        updated = updated.replace(
            "      - run: pnpm quality:fast\n",
            "      - if: github.event_name != 'workflow_dispatch'\n"
            "        run: pnpm change:check\n"
            "      - run: pnpm quality:fast\n",
            1,
        )
        changes.append("run the lightweight linkage check before unit tests")

    full_header = "  full:\n    needs: quality\n"
    full_guard = "  full:\n    needs: quality\n    if: github.event_name == 'workflow_dispatch'\n"
    if full_header in updated and full_guard not in updated:
        updated = updated.replace(full_header, full_guard, 1)
        changes.append("stop Full CI from running on ordinary pushes and pull requests")

    return updated, changes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument("--apply", action="store_true", help="write the reviewed migration")
    args = parser.parse_args()

    project = args.project.resolve()
    package_path = project / "package.json"
    agents_path = project / "AGENTS.md"
    workflow_path = project / ".github" / "workflows" / "quality.yml"
    if not package_path.is_file() or not agents_path.is_file():
        fail("Expected package.json and AGENTS.md at the project root")

    try:
        package = json.loads(read_text(package_path))
    except json.JSONDecodeError as error:
        fail(f"Invalid package.json: {error}")
    if not isinstance(package, dict):
        fail("package.json root must be an object")

    agents = read_text(agents_path)
    package_has_legacy = any(name in package.get("scripts", {}) for name in LEGACY_SCRIPTS)
    if not is_legacy_agents(agents) and not package_has_legacy:
        print("[OK] No generated v1.1-v1.6 Routine controls were detected.")
        return
    if not is_legacy_agents(agents):
        fail("Legacy scripts were found, but AGENTS.md is not a recognized generated template; migrate it manually to preserve custom rules")

    migrated_package, package_changes = migrate_package(package)
    migrated_agents = read_text(ASSETS / "AGENTS.template.md").replace(
        "{{PROJECT_DISPLAY_NAME}}", display_name(agents, package)
    )
    workflow = read_text(workflow_path) if workflow_path.is_file() else ""
    migrated_workflow, workflow_changes = migrate_ci(workflow)
    changes = ["replace legacy AGENTS.md with the Routine direct-test policy"]
    changes.extend(package_changes)
    changes.extend(workflow_changes)
    if not (project / "docs" / "changes.md").is_file():
        changes.append("add the single concise change record")
    if not (project / "scripts" / "quality" / "check-change-record.mjs").is_file():
        changes.append("add the lightweight change/test linkage script")
    commit_gate_files = {
        "scripts/quality/check-staged.mjs": "check-staged.mjs",
        "scripts/quality/check-commit-message.mjs": "check-commit-message.mjs",
        "scripts/quality/install-git-hooks.mjs": "install-git-hooks.mjs",
        ".githooks/pre-commit": "pre-commit",
        ".githooks/commit-msg": "commit-msg",
    }
    if any(not (project / relative).is_file() for relative in commit_gate_files):
        changes.append("add fast staged-file and Conventional Commit hooks")

    prefix = "[APPLY]" if args.apply else "[PLAN]"
    for change in changes:
        print(f"{prefix} {change}")
    if not args.apply:
        print("[NEXT] Review the plan, then rerun with --apply. No files were changed.")
        return

    write_text(agents_path, migrated_agents)
    write_text(package_path, json.dumps(migrated_package, ensure_ascii=False, indent=2) + "\n")
    if workflow:
        write_text(workflow_path, migrated_workflow)
    changes_path = project / "docs" / "changes.md"
    if not changes_path.is_file():
        write_text(changes_path, read_text(ASSETS / "changes.template.md"))
    checker_path = project / "scripts" / "quality" / "check-change-record.mjs"
    if not checker_path.is_file():
        write_text(checker_path, read_text(ASSETS / "check-change-record.mjs"))
    for relative, asset in commit_gate_files.items():
        target = project / relative
        if not target.is_file():
            write_text(target, read_text(ASSETS / asset))

    print("[OK] Legacy Routine controls migrated. Existing product code and archival documents were left untouched.")
    print("[NEXT] Run pnpm prepare once to enable the hooks, review the diff, and run one directly affected test file; do not run Full for this migration.")


if __name__ == "__main__":
    main()
