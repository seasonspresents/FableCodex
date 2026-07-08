from __future__ import annotations

try:
    from tests.support import (
        BIN,
        Path,
        ROOT,
        SCRIPTS,
        SKILL_ROOT,
        ScriptTestBase,
        SimpleNamespace,
        json,
        os,
        parse_routing_map,
        read_readme_fable_pin,
        read_skill_body,
        re,
        subprocess,
        sys,
        tempfile,
        textwrap,
    )
except ModuleNotFoundError:  # unittest discovery with tests/ as top-level.
    from support import (
        BIN,
        Path,
        ROOT,
        SCRIPTS,
        SKILL_ROOT,
        ScriptTestBase,
        SimpleNamespace,
        json,
        os,
        parse_routing_map,
        read_readme_fable_pin,
        read_skill_body,
        re,
        subprocess,
        sys,
        tempfile,
        textwrap,
    )


class ManifestDocsTests(ScriptTestBase):
    def test_manifest_json_files_are_valid(self) -> None:
        manifest_paths = [
            ROOT / ".agents" / "plugins" / "marketplace.json",
            ROOT / "plugins" / "codex-fable5" / ".codex-plugin" / "plugin.json",
            ROOT / "examples" / "hooks.json",
        ]
        for path in manifest_paths:
            with self.subTest(path=path):
                parsed = json.loads(path.read_text(encoding="utf-8"))
                self.assertIsInstance(parsed, dict)

    def test_marketplace_plugin_paths_resolve_to_skill(self) -> None:
        marketplace_path = ROOT / ".agents" / "plugins" / "marketplace.json"
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        root = ROOT.resolve()
        for plugin_entry in marketplace["plugins"]:
            with self.subTest(plugin=plugin_entry["name"]):
                plugin_root = (ROOT / plugin_entry["source"]["path"]).resolve()
                self.assertTrue(plugin_root.is_relative_to(root))

                plugin_manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
                plugin_manifest = json.loads(plugin_manifest_path.read_text(encoding="utf-8"))
                skills_root = (plugin_root / plugin_manifest["skills"]).resolve()
                skill_path = skills_root / plugin_manifest["name"] / "SKILL.md"

                self.assertTrue(plugin_root.is_dir())
                self.assertTrue(plugin_manifest_path.is_file())
                self.assertTrue(skills_root.is_relative_to(plugin_root))
                self.assertTrue(skills_root.is_dir())
                self.assertTrue(skill_path.is_file())

    def test_codex_runtime_manifest_contract_is_locally_enforced(self) -> None:
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual(marketplace["name"], "fablecodex")
        self.assertEqual(marketplace["interface"]["displayName"], "FableCodex")
        self.assertEqual(len(marketplace["plugins"]), 1)

        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "codex-fable5")
        self.assertEqual(entry["source"]["source"], "local")
        self.assertEqual(entry["source"]["path"], "./plugins/codex-fable5")
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")
        self.assertEqual(entry["category"], "Productivity")

        plugin_root = ROOT / entry["source"]["path"]
        plugin = json.loads((plugin_root / ".codex-plugin" / "plugin.json").read_text())
        interface = plugin["interface"]

        self.assertEqual(plugin["name"], entry["name"])
        self.assertRegex(plugin["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(plugin["skills"], "./skills/")
        self.assertTrue((plugin_root / plugin["skills"] / plugin["name"] / "SKILL.md").is_file())

        for key in [
            "displayName",
            "shortDescription",
            "longDescription",
            "developerName",
            "category",
            "capabilities",
            "defaultPrompt",
            "brandColor",
        ]:
            self.assertIn(key, interface)

        self.assertEqual(interface["displayName"], "Codex Fable5")
        self.assertEqual(interface["category"], entry["category"])
        self.assertIn("Skills", interface["capabilities"])
        self.assertRegex(interface["brandColor"], r"^#[0-9A-Fa-f]{6}$")
        self.assertLessEqual(len(interface["defaultPrompt"]), 3)
        self.assertTrue(any("codex-fable5" in prompt for prompt in interface["defaultPrompt"]))
        for prompt in interface["defaultPrompt"]:
            with self.subTest(prompt=prompt):
                self.assertLessEqual(len(prompt), 128)

    def test_codex_runtime_compatibility_doc_covers_observed_lifecycle(self) -> None:
        doc = (ROOT / "docs" / "CODEX_RUNTIME_COMPATIBILITY.md").read_text(encoding="utf-8")

        for snippet in [
            "codex-cli 0.128.0",
            "Codex Desktop/0.128.0",
            "codex-fable5@fablecodex",
            "codex-fable5:codex-fable5",
            "codex plugin marketplace add baskduf/FableCodex --ref v0.6.0",
            "plugin/install",
            "[plugins.\"codex-fable5@fablecodex\"]",
            "codex plugin add codex-fable5@fablecodex",
            "error: unrecognized subcommand 'add'",
            "most three entries",
            "128 characters",
            "CI should not require a local Codex binary",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, doc)

    def test_state_recovery_doc_covers_archive_first_paths(self) -> None:
        doc = (ROOT / "docs" / "STATE_RECOVERY.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for snippet in [
            "codex-fable5 doctor",
            "Corrupted `goals.json`",
            "Corrupted `findings.json`",
            "Stale Locks",
            "Interrupted Forced Plan Replacement",
            "Archive the file",
            "does not delete, rewrite, or repair user ledgers automatically",
            ".codex-fable5/",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, doc)
        self.assertIn("docs/STATE_RECOVERY.md", readme)

    def test_workflow_examples_cover_common_codex_tasks(self) -> None:
        doc = (ROOT / "examples" / "workflows.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for heading in [
            "## Debugging Unknown Failures",
            "## Frontend Visual Verification",
            "## Review-Only Analysis",
            "## Migration Or Refactor",
            "## Prompt Conversion",
            "## Provider Bridge Setup",
            "## Long-Running Goal Ledger",
            "## Release Dogfood Gate",
        ]:
            with self.subTest(heading=heading):
                self.assertIn(heading, doc)
        for snippet in [
            "When to use it:",
            "Prompt template:",
            "Expected FableCodex behavior:",
            "Verification evidence to collect:",
            "@codex-fable5",
            "does not grant Fable model capability",
            "Do not edit files",
            "codex-fable5 goals summary",
            "authorized access",
            "Run one multi-step task with a goal ledger",
            "docs/DOGFOOD_REPORT.md",
            "codex-fable5 findings gate",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, doc)
        self.assertIn("examples/workflows.md", readme)

    def test_dogfood_report_covers_three_representative_tasks(self) -> None:
        report = (ROOT / "docs" / "DOGFOOD_REPORT.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        releasing = (ROOT / "docs" / "RELEASING.md").read_text(encoding="utf-8")
        examples = (ROOT / "examples" / "workflows.md").read_text(encoding="utf-8")

        for snippet in [
            "Report date: 2026-07-08",
            "codex-cli 0.128.0",
            "debugPromptInputIncludesSkill: true",
            "Task 1 - Multi-Step Implementation With Goal Ledger",
            "Task 2 - Review-Only Findings Gate",
            "Task 3 - Debugging Unknown Failure With Hypotheses",
            "build/dogfood/per-52/task1/.codex-fable5/",
            "build/dogfood/per-52/task2/.codex-fable5/",
            "F001 [open] medium Release checklist omits dogfood review gate",
            "findings gate",
            "codex-fable5: findings gate passed",
            "1 resolved",
            "Competing hypotheses",
            "29 tests passed",
            "30 tests passed",
            "Summary: 6 passed, 1 skipped, 0 failed",
            "No new external GitHub or Linear issues were required",
            "python3 tools/verify_release.py",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, report)

        self.assertIn("docs/DOGFOOD_REPORT.md", readme)
        self.assertIn("docs/DOGFOOD_REPORT.md", releasing)
        self.assertIn("docs/DOGFOOD_REPORT.md", examples)

    def test_agents_template_is_safe_repo_adoption_guidance(self) -> None:
        template = (ROOT / "examples" / "AGENTS.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        for snippet in [
            "Copy this file to the root of a repository as `AGENTS.md`",
            "Active system, developer, safety, tool, sandbox, and user instructions outrank this file",
            "**Universal:**",
            "**Project-custom:**",
            "Inspect the workspace before making claims",
            "Verify every meaningful change",
            "Do not claim to be Claude, Fable, or Anthropic",
            "Do not assume hidden credentials",
            "Strict mode:",
            "Light mode:",
            "Review-only:",
            "No-ledger trivial task:",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, template)
        self.assertIn("examples/AGENTS.md", readme)

    def test_license_contains_full_agpl_text(self) -> None:
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")

        self.assertIn("GNU AFFERO GENERAL PUBLIC LICENSE", text)
        self.assertIn("Version 3, 19 November 2007", text)
        self.assertIn("TERMS AND CONDITIONS", text)
        self.assertIn("END OF TERMS AND CONDITIONS", text)
        self.assertGreaterEqual(len(text.splitlines()), 600)

    def test_license_metadata_declares_agpl_or_later(self) -> None:
        plugin = json.loads(
            (ROOT / "plugins" / "codex-fable5" / ".codex-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        notice = (ROOT / "NOTICE").read_text(encoding="utf-8")

        self.assertEqual(plugin["license"], "AGPL-3.0-or-later")
        self.assertIn("AGPL-3.0-or-later", readme)
        self.assertIn("AGPL-3.0-or-later", notice)

    def test_readme_localizations_cover_core_workflow(self) -> None:
        readmes = [
            "README.md",
            "README.ko.md",
            "README.ja.md",
            "README.zh-CN.md",
            "README.zh-TW.md",
        ]
        required_snippets = [
            "codex plugin marketplace add baskduf/FableCodex --ref v0.6.0",
            "codex plugin marketplace add baskduf/FableCodex --ref main",
            "codex plugin marketplace add ~/Desktop/FableCodex",
            "codex-fable5@fablecodex",
            "Codex Desktop",
            "codex plugin add",
            "error: unrecognized subcommand 'add'",
            "LiteLLM",
            "codex-fable5 goals create",
            "codex-fable5 doctor",
            "codex-fable5 goals summary",
            "codex-fable5 version",
            "codex-fable5 update",
            "codex-fable5 findings gate",
            ".codex-fable5/",
            "AGPL-3.0-or-later",
        ]

        for relative in readmes:
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                for other in readmes:
                    if other != relative:
                        self.assertIn(other, text)
                for snippet in required_snippets:
                    self.assertIn(snippet, text)
                self.assertNotIn("\ncodex plugin add codex-fable5@fablecodex\n", text)

    def test_skill_body_keeps_core_loop_concise(self) -> None:
        body = read_skill_body()
        routes = parse_routing_map(body)
        route_text = "\n".join(f"{signal} => {target}" for signal, target in routes)

        self.assertLessEqual(len(body.splitlines()), 90)
        self.assertLessEqual(len(body.split()), 950)
        for heading in ["## Non-Negotiables", "## Core Loop", "## Routing Map"]:
            self.assertIn(heading, body)

        self.assertIn("final verification gate", body)
        self.assertIn("Require the findings gate before final completion", body)
        self.assertIn("Communicate in Codex style", body)

        self.assertRegex(route_text, r"Multi-step.*task-routing\.md.*goal and findings gates")
        for target in [
            "references/task-routing.md",
            "references/operating-structure.md",
            "references/fable-to-codex-map.md",
            "references/coverage-matrix.md",
            "scripts/fable_coverage.py --source",
            "references/provider-bridge.md",
            "references/currentness-safety.md",
            "references/artifact-and-tooling.md",
            "references/connectors-and-mcp.md",
            "references/state-memory.md",
            "references/provenance.md",
        ]:
            self.assertIn(target, route_text)

    def test_provider_bridge_cites_current_official_sources(self) -> None:
        doc = (
            ROOT
            / "plugins"
            / "codex-fable5"
            / "skills"
            / "codex-fable5"
            / "references"
            / "provider-bridge.md"
        ).read_text(encoding="utf-8")

        for snippet in [
            "Verified on 2026-07-08",
            "codex-cli 0.128.0",
            "wire_api = \"responses\"",
            "Chat Completions support is deprecated",
            "OpenAI SDK compatibility layer",
            "`anthropic/` provider route",
            "`/responses` to `/chat/completions` bridge",
            "placeholder-based unless access is proven",
            "<your-anthropic-api-key>",
            "os.environ/ANTHROPIC_API_KEY",
            "does not provide model access",
            "https://developers.openai.com/codex/config-advanced#custom-model-providers",
            "https://docs.litellm.ai/docs/response_api",
            "https://docs.litellm.ai/docs/providers/anthropic",
            "https://platform.claude.com/docs/en/about-claude/models/overview",
            "https://platform.claude.com/docs/en/api/models/list",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, doc)
        self.assertNotIn("sk-ant-", doc)

    def test_security_privacy_review_covers_release_boundaries(self) -> None:
        doc = (ROOT / "docs" / "SECURITY_PRIVACY_REVIEW.md").read_text(encoding="utf-8")
        security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        releasing = (ROOT / "docs" / "RELEASING.md").read_text(encoding="utf-8")

        for snippet in [
            "Review date: 2026-07-08",
            "Provider bridge docs used a real-looking Anthropic-style key placeholder",
            "accepted option-like ref values",
            "Secret exposure",
            "Provider routing",
            "Local state privacy",
            "does not print full ledger contents",
            "refuses dirty worktrees",
            "deletes only its own temporary `CODEX_HOME`",
            "--source-check optional|required",
            "40-character commit SHA",
            "does not send an Authorization header",
            ".codex-fable5/",
            "python3 tools/verify_release.py --source-check required",
            "python3 tools/codex_plugin_smoke.py --case all",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, doc)

        self.assertIn("docs/SECURITY_PRIVACY_REVIEW.md", security)
        self.assertIn("docs/SECURITY_PRIVACY_REVIEW.md", releasing)

    def test_user_facing_files_do_not_contain_real_looking_key_placeholders(self) -> None:
        paths: list[Path] = []
        paths.extend(ROOT.glob("README*.md"))
        for directory in [
            ROOT / "docs",
            ROOT / "examples",
            ROOT / ".github",
            SKILL_ROOT / "references",
            SKILL_ROOT / "scripts",
        ]:
            for path in directory.rglob("*"):
                if path.is_file() and path.suffix in {".md", ".toml", ".yaml", ".yml", ".json", ".py"}:
                    paths.append(path)

        patterns = [
            (re.compile(r"sk-ant-[A-Za-z0-9_-]+"), "Anthropic-style key"),
            (re.compile(r"sk-proj-[A-Za-z0-9_-]+"), "OpenAI project key"),
            (re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"), "GitHub token"),
            (re.compile(r"xox[baprs]-[A-Za-z0-9-]+"), "Slack token"),
        ]

        for path in sorted(paths):
            text = path.read_text(encoding="utf-8")
            for pattern, label in patterns:
                with self.subTest(path=path.relative_to(ROOT).as_posix(), pattern=label):
                    self.assertIsNone(pattern.search(text))

    def test_connector_reference_covers_common_routing_examples(self) -> None:
        doc = (
            ROOT
            / "plugins"
            / "codex-fable5"
            / "skills"
            / "codex-fable5"
            / "references"
            / "connectors-and-mcp.md"
        ).read_text(encoding="utf-8")

        for snippet in [
            "GitHub And Repo Objects",
            "Browser And Chrome Visual Verification",
            "Linear Issue And Project Work",
            "Documents, Spreadsheets, And PDFs",
            "Connector Readback Versus Public Web Search",
            "Tool Discovery Pattern",
            "use `tool_search`",
            "Use connector readback",
            "public web search",
            "signed-in Chrome session",
            "PER-123",
            "Do not fabricate tool names",
            "https://developers.openai.com/codex/mcp",
            "https://developers.openai.com/codex/app/browser-use",
            "https://developers.openai.com/codex/app/chrome-extension",
            "https://developers.openai.com/codex/integrations/linear",
            "https://developers.openai.com/codex/integrations/github",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, doc)

    def test_plugin_version_is_documented_in_changelog(self) -> None:
        plugin = json.loads(
            (ROOT / "plugins" / "codex-fable5" / ".codex-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        self.assertIn(f"## {plugin['version']}", changelog)

    def test_release_notes_cover_v060_publication_boundary(self) -> None:
        notes = (ROOT / "docs" / "releases" / "v0.6.0.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

        for snippet in [
            "Status: ready to tag and publish after maintainer approval.",
            "codex plugin marketplace add baskduf/FableCodex --ref v0.6.0",
            "codex-cli 0.128.0",
            "codex-fable5@fablecodex",
            "codex-fable5:codex-fable5",
            "codex plugin add",
            "codex-fable5 doctor",
            "tools/codex_plugin_smoke.py",
            "tools/verify_release.py",
            "docs/DOGFOOD_REPORT.md",
            "Summary: 8 passed, 0 skipped, 0 failed",
            "codex-fable5 0.6.0",
            "debugPromptInputIncludesSkill: true",
            "Security",
            "Residual Limitations",
            "Tag creation, push, and GitHub release publication are intentionally deferred",
        ]:
            with self.subTest(snippet=snippet):
                self.assertIn(snippet, notes)

        for heading in ["### Added", "### Changed", "### Fixed", "### Security"]:
            with self.subTest(heading=heading):
                self.assertIn(heading, changelog)

    def test_oss_community_files_exist(self) -> None:
        required_paths = [
            "CODE_OF_CONDUCT.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
            "GOVERNANCE.md",
            "ROADMAP.md",
            "SECURITY.md",
            "SUPPORT.md",
            "docs/CODEX_RUNTIME_COMPATIBILITY.md",
            "docs/STATE_RECOVERY.md",
            "docs/SECURITY_PRIVACY_REVIEW.md",
            "docs/DOGFOOD_REPORT.md",
            "docs/releases/v0.6.0.md",
            ".gitignore",
            ".github/CODEOWNERS",
            ".github/dependabot.yml",
            ".github/ISSUE_TEMPLATE/bug_report.yml",
            ".github/ISSUE_TEMPLATE/feature_request.yml",
            ".github/ISSUE_TEMPLATE/config.yml",
            ".github/pull_request_template.md",
            ".github/workflows/ci.yml",
            "docs/RELEASING.md",
            "tools/verify_release.py",
            "examples/workflows.md",
        ]
        for relative in required_paths:
            with self.subTest(path=relative):
                path = ROOT / relative
                self.assertTrue(path.exists(), f"missing {relative}")
                self.assertGreater(path.stat().st_size, 0, f"empty {relative}")

    def test_repo_hygiene_files_cover_local_artifacts(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        codeowners = (ROOT / ".github" / "CODEOWNERS").read_text(encoding="utf-8")
        dependabot = (ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8")

        self.assertIn(".codex-fable5/", gitignore)
        self.assertIn("__pycache__/", gitignore)
        self.assertIn("build/", gitignore)
        self.assertIn("* @baskduf", codeowners)
        self.assertIn('package-ecosystem: "github-actions"', dependabot)
