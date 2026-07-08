# Dogfood Report

Report date: 2026-07-08

Scope: PER-52 release dogfood for local FableCodex behavior before v0.6. The dogfood used the local checkout at `/Users/admin/.codex/repo-inspection/FableCodex` and kept generated ledgers under ignored `build/dogfood/per-52/` state.

## Environment

- Codex runtime: `codex-cli 0.128.0`
- Codex Desktop user agent observed by local smoke: `Codex Desktop/0.128.0 (Mac OS 15.7.5; arm64)`
- FableCodex wrapper: `codex-fable5 0.6.0`
- Local skill path: `plugins/codex-fable5/skills/codex-fable5/SKILL.md`
- Skill invocation check: `python3 tools/codex_plugin_smoke.py --case local --json` installed and enabled `codex-fable5@fablecodex`, found `codex-fable5:codex-fable5`, and reported `debugPromptInputIncludesSkill: true`.

## Task 1 - Multi-Step Implementation With Goal Ledger

Prompt used:

```text
@codex-fable5 Create the PER-52 dogfood report, update release/workflow docs, keep local ledger evidence, and verify before closing the issue.
```

Skill invoked: yes. The local skill and relevant references were read: `SKILL.md`, `references/task-routing.md`, `references/operating-structure.md`, and `references/state-memory.md`.

State created:

- Directory: `build/dogfood/per-52/task1/.codex-fable5/`
- Ledger: `goals.json`
- Stories:
  - `G001 inspect`: loaded PER-52 criteria, local skill references, and local smoke evidence.
  - `G002 implement`: added this dogfood report, release checklist link, workflow example, and tests.
  - `G003 verify`: reserved for focused tests, local smoke evidence, and the release verifier.

Verification evidence:

- `python3 tools/codex_plugin_smoke.py --case local --json` passed with `debugPromptInputIncludesSkill: true`.
- `codex-fable5 goals checkpoint --id G001 --status complete ...` passed with concrete inspection evidence.
- `python3 -m unittest tests.test_manifests_docs tests.test_ci_release -v` passed after the report/docs patch with 30 tests.
- `python3 tools/verify_release.py` passed after the report/docs patch with `Summary: 6 passed, 1 skipped, 0 failed`.

Friction points:

- Dogfood evidence should not live only in ignored ledgers. Resolved by adding this committed report and linking it from release docs.
- Local smoke can emit a Codex runtime warning about warming the featured plugin cache with a 401 response. This did not block the local marketplace add, plugin install, skill enablement, debug prompt inclusion, uninstall, or marketplace removal, so no package change was needed.

## Task 2 - Review-Only Findings Gate

Prompt used:

```text
@codex-fable5 Analyze only. Review the release checklist for missing dogfood gates. Do not edit files during the review pass. Record accepted findings and run the findings gate before completion.
```

Skill invoked: yes. The findings behavior came from `references/task-routing.md` and the local `codex-fable5 findings` wrapper.

State created:

- Directory: `build/dogfood/per-52/task2/.codex-fable5/`
- Ledger: `findings.json`
- Finding opened: `F001 [open] medium Release checklist omits dogfood review gate`

Gate evidence:

- Before fix: `codex-fable5 findings gate` failed with one blocking finding, `F001`.
- Resolution path: update `docs/RELEASING.md` to require reviewing `docs/DOGFOOD_REPORT.md` before release, and update examples/tests so the dogfood gate remains discoverable.
- After fix: `codex-fable5 findings resolve --id F001 ...` marked the finding resolved with focused test evidence.
- Final gate: `codex-fable5 findings gate` reported `codex-fable5: findings gate passed`; `codex-fable5 findings status` reported `1 resolved`.

Friction points:

- Review-only mode worked well, but the report needed a durable repo surface. Resolved directly in docs.

## Task 3 - Debugging Unknown Failure With Hypotheses

Prompt used:

```text
@codex-fable5 Debug the focused test failure after cleaning up the old provider-key placeholder text. Reproduce it first, keep multiple hypotheses, patch the smallest confirmed cause, and verify.
```

Skill invoked: yes. The debugging behavior followed the investigation protocol in `references/task-routing.md`.

Reproduction:

```bash
python3 -m unittest tests.test_manifests_docs tests.test_ci_release -v
```

Observed failure: one focused docs test still expected the old wording `Provider bridge docs used a real-looking Anthropic key placeholder` after the report wording was changed to avoid mentioning the old key-shaped placeholder.

Competing hypotheses:

- The product doc no longer covered the provider-placeholder finding. Rejected: `docs/SECURITY_PRIVACY_REVIEW.md` still described the closed finding with safer wording.
- The test expectation was stale. Confirmed: the failure pointed to the exact outdated expected snippet.
- The docs read path or encoding changed. Rejected: adjacent snippets from the same file passed in the same test.

Fix:

- Updated the expected snippet in `tests/test_manifests_docs.py` to match the safer `Anthropic-style key placeholder` wording.

Verification evidence:

- Reran the focused suite: 29 tests passed.
- Reran the broad credential-pattern scan over README/docs/examples/.github/plugin references/scripts: no matches.

Friction points:

- Secret-scan commands that intentionally find no matches exit with code 1. This is correct for `rg`, but dogfood evidence should record that "no matches" is the expected success condition.

## Outcomes

Actionable friction resolved before release:

- Added this dogfood report as durable release evidence.
- Added release checklist coverage for `docs/DOGFOOD_REPORT.md`.
- Added a workflow example for release dogfood.
- Added tests that require the dogfood report, release link, workflow example, three task types, findings gate evidence, and debugging hypotheses.

No new external GitHub or Linear issues were required because the accepted dogfood findings were resolved directly before release.

## Final Gate

Commands run before closing PER-52:

```bash
python3 -m unittest tests.test_manifests_docs tests.test_ci_release -v
python3 tools/codex_plugin_smoke.py --case local --json
python3 tools/verify_release.py
```

Results:

- Focused tests: 30 tests passed.
- Local smoke: plugin installed/enabled from the local checkout and `debugPromptInputIncludesSkill: true`.
- Release verifier: `Summary: 6 passed, 1 skipped, 0 failed`.
- Findings gate: `codex-fable5: findings gate passed`.

The full release issue can run `python3 tools/verify_release.py --source-check required` again when cutting the tag.
