from __future__ import annotations

import shutil

try:
    from tests.support import (
        BIN,
        ROOT,
        ScriptTestBase,
        json,
        os,
        subprocess,
        tempfile,
        Path,
    )
except ModuleNotFoundError:  # unittest discovery with tests/ as top-level.
    from support import (
        BIN,
        ROOT,
        ScriptTestBase,
        json,
        os,
        subprocess,
        tempfile,
        Path,
    )


PLUGIN_ID = "codex-fable5@fablecodex"


class DoctorTests(ScriptTestBase):
    def run_doctor(self, cwd: Path, codex_home: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "PATH": f"{BIN}{os.pathsep}{os.environ['PATH']}"}
        if codex_home is not None:
            env["CODEX_HOME"] = str(codex_home)
        return subprocess.run(
            ["codex-fable5", "doctor"],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def write_config(self, codex_home: Path, enabled: bool = True) -> None:
        codex_home.mkdir(parents=True, exist_ok=True)
        value = "true" if enabled else "false"
        (codex_home / "config.toml").write_text(
            f'[plugins."{PLUGIN_ID}"]\n'
            f"enabled = {value}\n",
            encoding="utf-8",
        )

    def test_doctor_pass_reports_core_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp) / "work"
            codex_home = Path(tmp) / "codex-home"
            cwd.mkdir()
            self.write_config(codex_home)

            result = self.run_doctor(cwd, codex_home)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("codex-fable5 doctor", result.stdout)
            self.assertIn("OK manifest:", result.stdout)
            self.assertIn("OK skill:", result.stdout)
            self.assertIn("OK wrappers:", result.stdout)
            self.assertIn("OK scripts:", result.stdout)
            self.assertIn("OK state: no local state", result.stdout)
            self.assertIn("OK codex-config:", result.stdout)
            self.assertIn("Summary:", result.stdout)
            self.assertNotIn("FAIL ", result.stdout)

    def test_doctor_fails_on_invalid_state_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp) / "work"
            codex_home = Path(tmp) / "codex-home"
            state = cwd / ".codex-fable5"
            state.mkdir(parents=True)
            bad_findings = state / "findings.json"
            bad_findings.write_text("{not json\n", encoding="utf-8")
            self.write_config(codex_home)

            result = self.run_doctor(cwd, codex_home)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("FAIL state: findings ledger is not valid JSON", result.stdout)
            self.assertIn("hint: Archive before repair: mv", result.stdout)
            self.assertIn("findings.json.broken.<timestamp>", result.stdout)
            self.assertIn("Summary:", result.stdout)
            self.assertEqual(bad_findings.read_text(encoding="utf-8"), "{not json\n")

    def test_doctor_reports_state_summary_and_stale_lock_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp) / "work"
            codex_home = Path(tmp) / "codex-home"
            state = cwd / ".codex-fable5"
            state.mkdir(parents=True)
            (state / "state.lockdir").mkdir()
            (state / "findings.20260708T010000Z.archive.json").write_text(
                json.dumps({"findings": [{"id": "F999", "status": "open"}]}),
                encoding="utf-8",
            )
            (state / "goals.json").write_text(
                json.dumps(
                    {
                        "brief": "Doctor smoke",
                        "goals": [
                            {"id": "G001", "title": "one", "status": "complete"},
                            {"id": "G002", "title": "two", "status": "pending"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            (state / "findings.json").write_text(
                json.dumps(
                    {
                        "findings": [
                            {"id": "F001", "status": "open"},
                            {"id": "F002", "status": "resolved"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            (state / "ledger.jsonl").write_text('{"event": "ok"}\n', encoding="utf-8")
            self.write_config(codex_home)

            result = self.run_doctor(cwd, codex_home)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("WARN state-lock:", result.stdout)
            self.assertIn("archive it with: mv", result.stdout)
            self.assertIn("WARN state-archives:", result.stdout)
            self.assertIn("archived findings ledger", result.stdout)
            self.assertIn("goals: 1/2 complete (1 complete, 1 pending)", result.stdout)
            self.assertIn("findings: 1 open, 1 resolved", result.stdout)
            self.assertIn("ledger: valid JSONL", result.stdout)

    def test_doctor_warns_when_codex_config_is_missing_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp) / "work"
            codex_home = Path(tmp) / "codex-home"
            cwd.mkdir()

            result = self.run_doctor(cwd, codex_home)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("WARN codex-config:", result.stdout)
            self.assertIn(f"{PLUGIN_ID}", result.stdout)

    def test_update_hint_for_non_git_install_uses_desktop_enablement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / "FableCodex"
            shutil.copytree(ROOT / "plugins", clone / "plugins")

            result = subprocess.run(
                [
                    str(clone / "plugins" / "codex-fable5" / "bin" / "codex-fable5"),
                    "update",
                    "--ref",
                    "v0.6.0",
                    "--no-fetch",
                ],
                cwd=clone,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("codex plugin marketplace add baskduf/FableCodex --ref v0.6.0", result.stdout)
            self.assertIn("enable codex-fable5@fablecodex in Codex Desktop", result.stdout)
            self.assertNotIn("codex plugin add codex-fable5@fablecodex", result.stdout)
