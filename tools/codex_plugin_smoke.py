#!/usr/bin/env python3
"""Smoke-test FableCodex against a real Codex runtime.

This script intentionally uses a temporary CODEX_HOME so it can exercise the
marketplace and plugin lifecycle without modifying the user's main Codex
configuration.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "codex-fable5"
PLUGIN_ID = "codex-fable5@fablecodex"
SKILL_NAME = "codex-fable5:codex-fable5"
MARKETPLACE_NAME = "fablecodex"
REMOTE_SOURCE = "baskduf/FableCodex"


class SmokeError(RuntimeError):
    pass


class AppServerClient:
    def __init__(self, env: dict[str, str]) -> None:
        self.process = subprocess.Popen(
            ["codex", "app-server", "--listen", "stdio://"],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._next_id = 1
        self._messages: queue.Queue[dict[str, Any]] = queue.Queue()
        self._stderr: list[str] = []
        self._stdout_thread = threading.Thread(target=self._read_stdout, daemon=True)
        self._stderr_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self._stdout_thread.start()
        self._stderr_thread.start()

    def _read_stdout(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                self._messages.put(json.loads(line))
            except json.JSONDecodeError:
                self._messages.put({"method": "non_json_stdout", "params": {"line": line}})

    def _read_stderr(self) -> None:
        assert self.process.stderr is not None
        for line in self.process.stderr:
            self._stderr.append(line.rstrip("\n"))

    def request(self, method: str, params: dict[str, Any] | None = None, timeout: float = 20) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        payload = {"id": request_id, "method": method, "params": params}
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(payload) + "\n")
        self.process.stdin.flush()

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                message = self._messages.get(timeout=0.25)
            except queue.Empty:
                if self.process.poll() is not None:
                    break
                continue
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise SmokeError(f"{method} failed: {message['error']}")
            return message["result"]
        raise SmokeError(f"timed out waiting for app-server response to {method}")

    def close(self) -> list[str]:
        if self.process.stdin is not None:
            try:
                self.process.stdin.close()
            except OSError:
                pass
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=3)
        return self._stderr


def run_command(args: list[str], env: dict[str, str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, check=False)


def require_success(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode != 0:
        raise SmokeError(
            f"{label} failed with exit {result.returncode}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )


def plugin_version() -> str:
    manifest = ROOT / "plugins" / PLUGIN_NAME / ".codex-plugin" / "plugin.json"
    return str(json.loads(manifest.read_text(encoding="utf-8"))["version"])


def case_add_args(case: str, stable_ref: str, local_path: Path) -> list[str]:
    if case == "local":
        return [str(local_path)]
    if case == "stable":
        return [REMOTE_SOURCE, "--ref", stable_ref]
    if case == "main":
        return [REMOTE_SOURCE, "--ref", "main"]
    raise SmokeError(f"unknown smoke case {case!r}")


def find_plugin(marketplaces: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for marketplace in marketplaces:
        for plugin in marketplace.get("plugins", []):
            if plugin.get("id") == PLUGIN_ID:
                matches.append((marketplace, plugin))
    if not matches:
        raise SmokeError(f"{PLUGIN_ID} was not found in plugin/list output")
    return matches[0]


def find_skill(skills_result: dict[str, Any]) -> dict[str, Any]:
    for entry in skills_result.get("data", []):
        for skill in entry.get("skills", []):
            if skill.get("name") == SKILL_NAME:
                return skill
    raise SmokeError(f"{SKILL_NAME} was not found in skills/list output")


def wrapper_root_from_skill(skill_path: str) -> Path:
    path = Path(skill_path)
    # <plugin-root>/skills/codex-fable5/SKILL.md
    return path.parents[2]


def smoke_case(case: str, stable_ref: str, local_path: Path, keep_home: bool) -> dict[str, Any]:
    codex = shutil.which("codex")
    if codex is None:
        raise SmokeError("codex binary was not found on PATH")

    home = Path(tempfile.mkdtemp(prefix=f"fablecodex-{case}-home."))
    env = {**os.environ, "CODEX_HOME": str(home)}
    add_args = case_add_args(case, stable_ref, local_path)

    version = run_command(["codex", "--version"], env)
    require_success(version, "codex --version")

    add = run_command(["codex", "plugin", "marketplace", "add", *add_args], env)
    require_success(add, f"{case} marketplace add")

    client = AppServerClient(env)
    try:
        init = client.request(
            "initialize",
            {
                "clientInfo": {"name": "fablecodex-smoke", "version": "0.1.0"},
                "capabilities": {"experimentalApi": True},
            },
        )
        list_before = client.request("plugin/list", {"cwds": [str(home)]})
        marketplace, plugin_before = find_plugin(list_before["marketplaces"])
        install = client.request(
            "plugin/install",
            {"pluginName": PLUGIN_NAME, "marketplacePath": marketplace["path"]},
        )
        list_after = client.request("plugin/list", {"cwds": [str(home)]})
        _, plugin_after = find_plugin(list_after["marketplaces"])
        skills = client.request("skills/list", {"cwds": [str(home)], "forceReload": True})
        skill = find_skill(skills)
    finally:
        stderr = client.close()

    if not plugin_after.get("installed") or not plugin_after.get("enabled"):
        raise SmokeError(f"{PLUGIN_ID} was not installed and enabled after plugin/install")
    if not skill.get("enabled"):
        raise SmokeError(f"{SKILL_NAME} was present but disabled")

    plugin_root = wrapper_root_from_skill(skill["path"])
    wrapper = plugin_root / "bin" / "codex-fable5"
    if not wrapper.is_file():
        raise SmokeError(f"installed wrapper was not found at {wrapper}")
    wrapper_version = run_command([str(wrapper), "version"], env, cwd=home)
    require_success(wrapper_version, f"{case} wrapper version")

    prompt = run_command(["codex", "debug", "prompt-input", "@codex-fable5 Say hello"], env, cwd=home)
    require_success(prompt, f"{case} debug prompt-input")
    if "Codex Fable5" not in prompt.stdout or SKILL_NAME not in prompt.stdout:
        raise SmokeError("debug prompt input did not include the enabled plugin and skill")

    uninstall_result = client_uninstall(env, home)

    upgrade_summary: dict[str, Any] | None = None
    if case in {"stable", "main"}:
        upgrade = run_command(["codex", "plugin", "marketplace", "upgrade", MARKETPLACE_NAME], env)
        require_success(upgrade, f"{case} marketplace upgrade")
        upgrade_summary = {"stdout": upgrade.stdout.strip()}

    remove = run_command(["codex", "plugin", "marketplace", "remove", MARKETPLACE_NAME], env)
    require_success(remove, f"{case} marketplace remove")

    summary = {
        "case": case,
        "codexVersion": version.stdout.strip(),
        "userAgent": init["userAgent"],
        "codexHome": str(home),
        "marketplacePath": marketplace["path"],
        "pluginBefore": {"installed": plugin_before["installed"], "enabled": plugin_before["enabled"]},
        "pluginAfter": {"installed": plugin_after["installed"], "enabled": plugin_after["enabled"]},
        "install": install,
        "skill": {"name": skill["name"], "path": skill["path"], "scope": skill["scope"], "enabled": skill["enabled"]},
        "wrapper": str(wrapper),
        "wrapperVersion": wrapper_version.stdout.strip().splitlines()[0],
        "debugPromptInputIncludesSkill": True,
        "uninstall": uninstall_result,
        "upgrade": upgrade_summary,
        "remove": {"stdout": remove.stdout.strip()},
        "stderrWarnings": [line for line in stderr if '"level":"WARN"' in line or '"level":"ERROR"' in line],
    }

    if not keep_home:
        shutil.rmtree(home, ignore_errors=True)
        summary["codexHomeRemoved"] = True
    else:
        summary["codexHomeRemoved"] = False
    return summary


def client_uninstall(env: dict[str, str], home: Path) -> dict[str, Any]:
    client = AppServerClient(env)
    try:
        client.request(
            "initialize",
            {
                "clientInfo": {"name": "fablecodex-smoke", "version": "0.1.0"},
                "capabilities": {"experimentalApi": True},
            },
        )
        result = client.request("plugin/uninstall", {"pluginId": PLUGIN_ID})
        after = client.request("plugin/list", {"cwds": [str(home)]})
        _, plugin = find_plugin(after["marketplaces"])
    finally:
        client.close()
    if plugin.get("installed") or plugin.get("enabled"):
        raise SmokeError(f"{PLUGIN_ID} was still installed/enabled after uninstall")
    return {"result": result, "pluginAfter": {"installed": plugin["installed"], "enabled": plugin["enabled"]}}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--case",
        choices=["all", "local", "stable", "main"],
        default="all",
        help="Which install path to smoke-test.",
    )
    parser.add_argument(
        "--stable-ref",
        default=f"v{plugin_version()}",
        help="Stable release ref to test for the stable case.",
    )
    parser.add_argument(
        "--local-path",
        type=Path,
        default=ROOT,
        help="Local FableCodex checkout used for the local case.",
    )
    parser.add_argument(
        "--keep-home",
        action="store_true",
        help="Keep temporary CODEX_HOME directories for inspection.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cases = ["local", "stable", "main"] if args.case == "all" else [args.case]
    results = []
    try:
        for case in cases:
            result = smoke_case(case, args.stable_ref, args.local_path.resolve(), args.keep_home)
            results.append(result)
            if not args.json:
                print(
                    f"ok {case}: {result['codexVersion']} "
                    f"skill={result['skill']['name']} wrapper={result['wrapperVersion']}"
                )
    except SmokeError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc), "results": results}, indent=2))
        else:
            print(f"codex_plugin_smoke: {exc}", file=sys.stderr)
        return 1

    payload = {"ok": True, "results": results}
    if args.json:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
