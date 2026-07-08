#!/usr/bin/env python3
"""Run FableCodex maintainer verification from one command."""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FABLE_SOURCE_PATH = ROOT / "build" / "fable5" / "CLAUDE-FABLE-5.md"
FABLE_SOURCE_MARKER = "Fable 5"


@dataclass(frozen=True)
class Step:
    name: str
    command: list[str]


class Summary:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.planned = 0

    def pass_(self) -> None:
        self.passed += 1

    def fail(self) -> None:
        self.failed += 1

    def skip(self) -> None:
        self.skipped += 1

    def plan(self) -> None:
        self.planned += 1

    def exit_code(self) -> int:
        return 1 if self.failed else 0

    def print(self) -> None:
        if self.planned:
            print(
                f"Summary: {self.passed} passed, {self.skipped} skipped, "
                f"{self.failed} failed, {self.planned} planned"
            )
        else:
            print(f"Summary: {self.passed} passed, {self.skipped} skipped, {self.failed} failed")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def command_text(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def python_files() -> list[str]:
    paths: list[Path] = []
    for pattern in [
        "plugins/codex-fable5/skills/codex-fable5/scripts/*.py",
        "tools/*.py",
        "tests/*.py",
    ]:
        paths.extend(ROOT.glob(pattern))
    return [rel(path) for path in sorted(paths)]


def wrapper_files() -> list[str]:
    return [
        "plugins/codex-fable5/bin/codex-fable5",
        "plugins/codex-fable5/bin/codex-findings",
        "plugins/codex-fable5/bin/codex-goals",
    ]


def build_steps() -> list[Step]:
    coverage = "plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py"
    return [
        Step("unit tests", ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"]),
        Step("python compile", ["python3", "-m", "py_compile", *python_files()]),
        *[Step(f"shell syntax: {path}", ["sh", "-n", path]) for path in wrapper_files()],
        Step("coverage matrix", ["python3", coverage]),
    ]


def print_stream(label: str, text: str) -> None:
    text = text.strip()
    if not text:
        return
    print(f"{label}:")
    print(text)


def run_step(step: Step, summary: Summary, dry_run: bool, timeout: int) -> bool:
    command = command_text(step.command)
    if dry_run:
        summary.plan()
        print(f"DRY RUN {step.name}: {command}")
        return True

    print(f"RUN {step.name}: {command}")
    started = time.monotonic()
    try:
        result = subprocess.run(
            step.command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        summary.fail()
        print(f"FAIL {step.name}: timed out after {timeout}s")
        print(f"command: {command}")
        print_stream("stdout", exc.stdout or "")
        print_stream("stderr", exc.stderr or "")
        return False

    elapsed = time.monotonic() - started
    if result.returncode == 0:
        summary.pass_()
        print(f"PASS {step.name} ({elapsed:.1f}s)")
        return True

    summary.fail()
    print(f"FAIL {step.name}: exit {result.returncode} ({elapsed:.1f}s)")
    print(f"command: {command}")
    print_stream("stdout", result.stdout)
    print_stream("stderr", result.stderr)
    return False


def read_fable_pin() -> str:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    match = re.search(
        r"`elder-plinius/CL4R1T4S`\s+`ANTHROPIC/CLAUDE-FABLE-5\.md`\s+"
        r"at commit\s+`([0-9a-f]{40})`",
        readme,
    )
    if match is None:
        raise RuntimeError("pinned FABLE-5 SHA not found in README.md")
    return match.group(1)


def fetch_upstream_source(summary: Summary, mode: str, dry_run: bool, timeout: int) -> bool:
    if mode == "skip":
        summary.skip()
        print("SKIP upstream source: pass --source-check optional or --source-check required to fetch it")
        return False

    try:
        pin = read_fable_pin()
    except RuntimeError as exc:
        if mode == "optional":
            summary.skip()
            print(f"SKIP upstream source: {exc}")
            return False
        summary.fail()
        print(f"FAIL upstream source: {exc}")
        return False

    url = f"https://raw.githubusercontent.com/elder-plinius/CL4R1T4S/{pin}/ANTHROPIC/CLAUDE-FABLE-5.md"
    if dry_run:
        summary.plan()
        print(f"DRY RUN upstream source: fetch {url} -> {rel(FABLE_SOURCE_PATH)}")
        return True

    print(f"RUN upstream source: fetch {url} -> {rel(FABLE_SOURCE_PATH)}")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except (OSError, UnicodeDecodeError, urllib.error.URLError) as exc:
        if mode == "optional":
            summary.skip()
            print(f"SKIP upstream source: {exc}")
            return False
        summary.fail()
        print(f"FAIL upstream source: {exc}")
        print(f"url: {url}")
        return False

    if FABLE_SOURCE_MARKER not in body:
        message = f"downloaded source did not contain {FABLE_SOURCE_MARKER!r}"
        if mode == "optional":
            summary.skip()
            print(f"SKIP upstream source: {message}")
            return False
        summary.fail()
        print(f"FAIL upstream source: {message}")
        print(f"url: {url}")
        return False

    FABLE_SOURCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FABLE_SOURCE_PATH.write_text(body, encoding="utf-8")
    elapsed = time.monotonic() - started
    summary.pass_()
    print(f"PASS upstream source ({elapsed:.1f}s): {rel(FABLE_SOURCE_PATH)}")
    return True


def source_coverage_step() -> Step:
    return Step(
        "coverage matrix with pinned source",
        [
            "python3",
            "plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py",
            "--source",
            rel(FABLE_SOURCE_PATH),
        ],
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-check",
        choices=["skip", "optional", "required"],
        default="skip",
        help=(
            "Controls the pinned upstream FABLE source validation. "
            "'skip' is offline-only, 'optional' skips on network/source failure, "
            "and 'required' fails on network/source failure."
        ),
    )
    parser.add_argument("--timeout", type=int, default=300, help="Per-command timeout in seconds.")
    parser.add_argument("--dry-run", action="store_true", help="Print the planned checks without running them.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = Summary()

    print("FableCodex release verification")
    for step in build_steps():
        run_step(step, summary, args.dry_run, args.timeout)

    if fetch_upstream_source(summary, args.source_check, args.dry_run, args.timeout):
        run_step(source_coverage_step(), summary, args.dry_run, args.timeout)

    summary.print()
    return summary.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
