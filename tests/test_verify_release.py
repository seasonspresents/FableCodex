from __future__ import annotations

try:
    from tests.support import ROOT, ScriptTestBase, subprocess, sys
except ModuleNotFoundError:  # unittest discovery with tests/ as top-level.
    from support import ROOT, ScriptTestBase, subprocess, sys


class VerifyReleaseTests(ScriptTestBase):
    def test_verify_release_dry_run_lists_required_checks(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/verify_release.py", "--dry-run"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DRY RUN unit tests: python3 -m unittest discover -s tests -v", result.stdout)
        self.assertIn("DRY RUN python compile: python3 -m py_compile", result.stdout)
        self.assertIn("tools/verify_release.py", result.stdout)
        self.assertIn("DRY RUN shell syntax: plugins/codex-fable5/bin/codex-fable5", result.stdout)
        self.assertIn("DRY RUN shell syntax: plugins/codex-fable5/bin/codex-findings", result.stdout)
        self.assertIn("DRY RUN shell syntax: plugins/codex-fable5/bin/codex-goals", result.stdout)
        self.assertIn("DRY RUN coverage matrix: python3 plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py", result.stdout)
        self.assertIn("SKIP upstream source", result.stdout)
        self.assertIn("Summary:", result.stdout)

    def test_verify_release_dry_run_required_source_lists_pinned_source_check(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/verify_release.py", "--dry-run", "--source-check", "required"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("DRY RUN upstream source: fetch https://raw.githubusercontent.com/elder-plinius/CL4R1T4S/", result.stdout)
        self.assertIn("build/fable5/CLAUDE-FABLE-5.md", result.stdout)
        self.assertIn(
            "DRY RUN coverage matrix with pinned source: python3 plugins/codex-fable5/skills/codex-fable5/scripts/fable_coverage.py --source build/fable5/CLAUDE-FABLE-5.md",
            result.stdout,
        )
