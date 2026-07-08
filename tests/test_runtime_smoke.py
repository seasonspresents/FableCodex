from __future__ import annotations

try:
    from tests.support import ROOT, subprocess, sys
except ModuleNotFoundError:  # unittest discovery with tests/ as top-level.
    from support import ROOT, subprocess, sys

import unittest


class RuntimeSmokeToolTests(unittest.TestCase):
    def test_codex_plugin_smoke_help_documents_install_cases(self) -> None:
        script = ROOT / "tools" / "codex_plugin_smoke.py"
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--case", result.stdout)
        self.assertIn("stable", result.stdout)
        self.assertIn("main", result.stdout)
        self.assertIn("local", result.stdout)
        self.assertIn("--keep-home", result.stdout)

    def test_runtime_compatibility_doc_points_to_smoke_tool(self) -> None:
        doc = (ROOT / "docs" / "CODEX_RUNTIME_COMPATIBILITY.md").read_text(encoding="utf-8")

        for snippet in [
            "python3 tools/codex_plugin_smoke.py --case all",
            "temporary `CODEX_HOME`",
            "codex debug prompt-input '@codex-fable5 Say hello'",
            "codex-fable5 version",
            "plugin/uninstall",
            "codex plugin marketplace upgrade",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, doc)
