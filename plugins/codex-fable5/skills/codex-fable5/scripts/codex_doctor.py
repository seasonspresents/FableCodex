#!/usr/bin/env python3
"""Installed-package diagnostics for Codex Fable5."""

from __future__ import annotations

import importlib.util
import json
import os
import py_compile
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_ID = "codex-fable5@fablecodex"
WRAPPERS = ["codex-fable5", "codex-findings", "codex-goals"]
PYTHON_SCRIPTS = [
    "codex_fable_state.py",
    "codex_findings.py",
    "codex_goals.py",
    "codex_doctor.py",
    "fable_coverage.py",
    "make_litellm_config.py",
]


class Reporter:
    def __init__(self) -> None:
        self.counts = {"OK": 0, "WARN": 0, "FAIL": 0}

    def emit(self, status: str, label: str, message: str, hint: str = "") -> None:
        self.counts[status] += 1
        print(f"{status} {label}: {message}")
        if hint:
            print(f"  hint: {hint}")

    def ok(self, label: str, message: str) -> None:
        self.emit("OK", label, message)

    def warn(self, label: str, message: str, hint: str = "") -> None:
        self.emit("WARN", label, message, hint)

    def fail(self, label: str, message: str, hint: str = "") -> None:
        self.emit("FAIL", label, message, hint)

    def finish(self) -> int:
        print(
            "Summary: "
            f"{self.counts['OK']} ok, {self.counts['WARN']} warn, {self.counts['FAIL']} fail"
        )
        return 1 if self.counts["FAIL"] else 0


def paths() -> dict[str, Path]:
    script = Path(__file__).resolve()
    skill_root = script.parents[1]
    plugin_root = script.parents[3]
    return {
        "script": script,
        "scripts": script.parent,
        "skill_root": skill_root,
        "skill": skill_root / "SKILL.md",
        "plugin_root": plugin_root,
        "manifest": plugin_root / ".codex-plugin" / "plugin.json",
        "bin": plugin_root / "bin",
    }


def read_json_file(path: Path, label: str) -> tuple[Any | None, str]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), ""
    except OSError as exc:
        return None, f"{label} could not be read ({exc})"
    except json.JSONDecodeError as exc:
        return None, f"{label} is not valid JSON ({path}:{exc.lineno}:{exc.colno}: {exc.msg})"


def check_manifest(reporter: Reporter, manifest_path: Path) -> dict[str, Any] | None:
    data, error = read_json_file(manifest_path, "plugin manifest")
    if error:
        reporter.fail("manifest", error, "Reinstall the plugin or restore .codex-plugin/plugin.json.")
        return None
    if not isinstance(data, dict):
        reporter.fail("manifest", f"plugin manifest must be a JSON object ({manifest_path})")
        return None

    name = data.get("name")
    version = data.get("version")
    skills = data.get("skills")
    if not isinstance(name, str) or not name:
        reporter.fail("manifest", "missing string field 'name'", "Restore the packaged manifest.")
        return data
    if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version):
        reporter.fail("manifest", "field 'version' must be semantic version text")
        return data
    if not isinstance(skills, str) or not skills:
        reporter.fail("manifest", "missing string field 'skills'", "Point it at the packaged skills directory.")
        return data

    reporter.ok("manifest", f"{name} {version} at {manifest_path}")
    return data


def check_skill(reporter: Reporter, path_info: dict[str, Path], manifest: dict[str, Any] | None) -> None:
    name = "codex-fable5"
    skills_path = "./skills/"
    if manifest:
        name = str(manifest.get("name") or name)
        skills_path = str(manifest.get("skills") or skills_path)

    skill_path = path_info["plugin_root"] / skills_path / name / "SKILL.md"
    try:
        text = skill_path.read_text(encoding="utf-8")
    except OSError as exc:
        reporter.fail("skill", f"could not read {skill_path} ({exc})", "Restore the packaged skill tree.")
        return

    match = re.match(r"\A---\r?\n(?P<frontmatter>.*?)\r?\n---\r?\n(?P<body>.*)\Z", text, re.DOTALL)
    if match is None:
        reporter.fail("skill", "SKILL.md is missing YAML frontmatter", "Restore the packaged SKILL.md.")
        return
    frontmatter = match.group("frontmatter")
    body = match.group("body").strip()
    if "name:" not in frontmatter or "description:" not in frontmatter:
        reporter.fail("skill", "frontmatter must include name and description")
        return
    if not body:
        reporter.fail("skill", "SKILL.md body is empty")
        return

    reporter.ok("skill", f"{skill_path}")


def check_wrappers(reporter: Reporter, bin_dir: Path) -> None:
    missing: list[str] = []
    not_executable: list[str] = []
    for name in WRAPPERS:
        path = bin_dir / name
        if not path.is_file():
            missing.append(name)
        elif not os.access(path, os.X_OK):
            not_executable.append(name)

    if missing or not_executable:
        bits = []
        if missing:
            bits.append(f"missing: {', '.join(missing)}")
        if not_executable:
            bits.append(f"not executable: {', '.join(not_executable)}")
        reporter.fail("wrappers", "; ".join(bits), "Reinstall the plugin or run chmod +x on packaged wrappers.")
        return

    reporter.ok("wrappers", f"{len(WRAPPERS)} executable wrappers in {bin_dir}")


def import_script(path: Path, module_name: str, scripts_dir: Path) -> None:
    py_compile.compile(str(path), doraise=True)
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load import spec for {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def check_python_scripts(reporter: Reporter, scripts_dir: Path) -> None:
    failures: list[str] = []
    for name in PYTHON_SCRIPTS:
        path = scripts_dir / name
        if not path.is_file():
            failures.append(f"{name}: missing")
            continue
        try:
            import_script(path, f"_codex_fable5_doctor_{path.stem}", scripts_dir)
        except Exception as exc:  # noqa: BLE001 - diagnostic should report any import failure.
            failures.append(f"{name}: {exc}")

    if failures:
        reporter.fail("scripts", "; ".join(failures), "Run python3 -m py_compile on the package scripts.")
        return

    reporter.ok("scripts", f"{len(PYTHON_SCRIPTS)} Python scripts compile and import")


def archive_hint(path: Path, next_step: str) -> str:
    return f"Archive before repair: mv {path} {path}.broken.<timestamp>; then {next_step}"


def load_state_json(reporter: Reporter, path: Path, label: str, next_step: str) -> Any | None:
    data, error = read_json_file(path, label)
    if error:
        reporter.fail("state", error, archive_hint(path, next_step))
        return None
    return data


def count_statuses(items: list[Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        if isinstance(item, dict):
            status = item.get("status", "unknown")
        else:
            status = "invalid"
        if not isinstance(status, str) or not status:
            status = "unknown"
        counts[status] = counts.get(status, 0) + 1
    return counts


def format_counts(counts: dict[str, int]) -> str:
    if not counts:
        return "none"
    return ", ".join(f"{count} {status}" for status, count in sorted(counts.items()))


def validate_jsonl(reporter: Reporter, path: Path) -> bool:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        reporter.fail(
            "state",
            f"ledger could not be read ({exc})",
            archive_hint(path, "rerun the command that should append ledger events."),
        )
        return False
    for index, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            json.loads(line)
        except json.JSONDecodeError as exc:
            reporter.fail(
                "state",
                f"ledger line {index} is not valid JSON ({path}:{exc.lineno}:{exc.colno}: {exc.msg})",
                archive_hint(path, "keep the archived file for audit history."),
            )
            return False
    return True


def check_state(reporter: Reporter, cwd: Path) -> None:
    state_dir = cwd / ".codex-fable5"
    if not state_dir.exists():
        reporter.ok("state", f"no local state in {cwd}")
        return
    if not state_dir.is_dir():
        reporter.fail(
            "state",
            f"{state_dir} is not a directory",
            archive_hint(state_dir, "rerun the command from the project root."),
        )
        return

    summaries: list[str] = []
    failed_before = reporter.counts["FAIL"]

    lockdir = state_dir / "state.lockdir"
    if lockdir.exists():
        reporter.warn(
            "state-lock",
            f"fallback lock directory is present at {lockdir}",
            f"If no codex-fable5 command is running, archive it with: mv {lockdir} {lockdir}.stale.<timestamp>",
        )

    archives = sorted(state_dir.glob("findings.*.archive.json"))
    if archives:
        reporter.warn(
            "state-archives",
            f"{len(archives)} archived findings ledger(s) present",
            "Review archived findings before deleting them; restore by copying one to .codex-fable5/findings.json if a forced replacement was interrupted.",
        )

    goals_path = state_dir / "goals.json"
    if goals_path.exists():
        goals_data = load_state_json(
            reporter,
            goals_path,
            "goal plan",
            "recreate a plan with `codex-fable5 goals create ...` or restore the archived file.",
        )
        if isinstance(goals_data, dict) and isinstance(goals_data.get("goals"), list):
            goals = goals_data["goals"]
            complete = sum(1 for goal in goals if isinstance(goal, dict) and goal.get("status") == "complete")
            summaries.append(f"goals: {complete}/{len(goals)} complete ({format_counts(count_statuses(goals))})")
        elif goals_data is not None:
            reporter.fail(
                "state",
                f"goal plan field 'goals' must be a list ({goals_path})",
                archive_hint(goals_path, "recreate a plan with `codex-fable5 goals create ...`."),
            )
    else:
        summaries.append("goals: no plan")

    findings_path = state_dir / "findings.json"
    if findings_path.exists():
        findings_data = load_state_json(
            reporter,
            findings_path,
            "findings ledger",
            "restore a valid findings ledger or start a new one with `codex-fable5 findings add ...`.",
        )
        if isinstance(findings_data, dict) and isinstance(findings_data.get("findings"), list):
            findings = findings_data["findings"]
            summaries.append(f"findings: {format_counts(count_statuses(findings))}")
        elif findings_data is not None:
            reporter.fail(
                "state",
                f"findings ledger field 'findings' must be a list ({findings_path})",
                archive_hint(findings_path, "restore a valid findings ledger or start a new one."),
            )
    else:
        summaries.append("findings: 0 findings")

    ledger_path = state_dir / "ledger.jsonl"
    if ledger_path.exists() and validate_jsonl(reporter, ledger_path):
        summaries.append("ledger: valid JSONL")

    if reporter.counts["FAIL"] == failed_before:
        reporter.ok("state", "; ".join(summaries))


def plugin_table(text: str) -> list[str] | None:
    inside = False
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if inside:
                break
            inside = stripped == f'[plugins."{PLUGIN_ID}"]'
            continue
        if inside:
            lines.append(line)
    return lines if inside else None


def check_codex_config(reporter: Reporter) -> None:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    config = codex_home / "config.toml"
    try:
        text = config.read_text(encoding="utf-8")
    except FileNotFoundError:
        reporter.warn(
            "codex-config",
            f"{config} not found",
            "Add the marketplace source, then enable codex-fable5@fablecodex in Codex Desktop.",
        )
        return
    except OSError as exc:
        reporter.warn("codex-config", f"could not read {config} ({exc})")
        return

    table = plugin_table(text)
    if table is None:
        reporter.warn(
            "codex-config",
            f"{PLUGIN_ID} is not listed in {config}",
            "Add the marketplace source, then enable the plugin in Codex Desktop.",
        )
        return

    body = "\n".join(table)
    if re.search(r"(?m)^\s*enabled\s*=\s*true\s*(?:#.*)?$", body):
        reporter.ok("codex-config", f"{PLUGIN_ID} enabled in {config}")
    else:
        reporter.warn(
            "codex-config",
            f"{PLUGIN_ID} is listed but not enabled in {config}",
            "Enable the plugin in Codex Desktop, then restart or reload Codex.",
        )


def main() -> int:
    reporter = Reporter()
    path_info = paths()
    print("codex-fable5 doctor")
    manifest = check_manifest(reporter, path_info["manifest"])
    check_skill(reporter, path_info, manifest)
    check_wrappers(reporter, path_info["bin"])
    check_python_scripts(reporter, path_info["scripts"])
    check_state(reporter, Path.cwd())
    check_codex_config(reporter)
    return reporter.finish()


if __name__ == "__main__":
    raise SystemExit(main())
