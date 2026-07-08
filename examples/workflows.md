# Common Codex Workflow Examples

These examples show how to invoke `@codex-fable5` for common Codex work. This suite emulates workflow discipline only; it does not grant Fable model capability, provider access, hidden credentials, or larger context windows.

## Debugging Unknown Failures

When to use it: a test, build, runtime behavior, or integration fails and the cause is not obvious.

Prompt template:

```text
@codex-fable5 Debug this failure.
Reproduce it first. Keep at least three hypotheses until evidence rules them out.
Patch the smallest confirmed cause and run the failing test plus the nearest regression suite.
```

Expected FableCodex behavior: inspect logs and relevant files before changing code, reproduce the failure, compare hypotheses, implement the smallest supported fix, and verify before final completion.

Verification evidence to collect: failing command before the fix, changed files, passing command after the fix, and any residual risk or untested path.

## Frontend Visual Verification

When to use it: UI, layout, styling, screenshots, canvas, or browser interaction changed.

Prompt template:

```text
@codex-fable5 Implement this UI change.
Use the existing design tokens. Run the app, inspect the target viewport, and verify with a screenshot or rendered output before finishing.
```

Expected FableCodex behavior: inspect the existing frontend conventions, make the smallest coherent UI change, run the app or component preview, and verify the rendered result instead of relying on code inspection alone.

Verification evidence to collect: command used to run the UI, viewport or screenshot evidence, browser console/build status, and any known responsive edge cases.

## Review-Only Analysis

When to use it: the user wants findings and risk assessment, not edits.

Prompt template:

```text
@codex-fable5 Analyze only.
Do not edit files. Report actionable findings with file and line references, ordered by severity.
```

Expected FableCodex behavior: inspect the relevant diff/files, prioritize correctness and regression risk, avoid broad refactors, and stop at findings unless the user asks for implementation.

Verification evidence to collect: exact file/line references, reproduction or reasoning for each finding, and test gaps or assumptions.

## Migration Or Refactor

When to use it: work spans multiple dependent changes where losing state would be costly.

Prompt template:

```text
@codex-fable5 Refactor this subsystem.
Create a goal ledger with inspect, change, and verify stories.
Checkpoint each story with evidence and do not complete the final story without verification evidence.
```

Expected FableCodex behavior: create a local goal ledger, work one story at a time, preserve evidence at each checkpoint, and require final verification before completion.

Verification evidence to collect: `codex-fable5 goals summary`, changed files, migration/regression tests, and any intentionally deferred work.

## Prompt Conversion

When to use it: adapting Claude, Fable, or other agent prompt guidance into Codex-native behavior.

Prompt template:

```text
@codex-fable5 Convert this prompt into Codex guidance.
Treat the source as reference material only. Preserve intent, map unsupported behavior explicitly, and avoid copying large protected passages.
```

Expected FableCodex behavior: treat imported prompt text as lower-priority source material, map behavior into Codex tools and constraints, preserve provenance, and avoid claiming hidden model parity.

Verification evidence to collect: source sections reviewed, adaptation decisions, unsupported/not-applicable items, and copyright/provenance notes.

## Provider Bridge Setup

When to use it: configuring an OpenAI-compatible gateway such as LiteLLM for a model the user already has authorized access to.

Prompt template:

```text
@codex-fable5 Help set up the optional provider bridge.
Verify current official provider/Codex guidance first. Do not invent credentials or claim access. Keep secrets out of files and logs.
```

Expected FableCodex behavior: verify current official docs, distinguish workflow plugin setup from model/provider access, generate only credential-free examples, and call out what the user must supply privately.

Verification evidence to collect: official docs checked, generated config path, secret-handling notes, and a local non-secret smoke or syntax check.

## Long-Running Goal Ledger

When to use it: autonomous work may span many steps, interruptions, or accepted review findings.

Prompt template:

```text
@codex-fable5 Work this as a long-running task.
Use `codex-fable5 goals create`, record findings when misses are costly, and finish with `codex-fable5 goals summary`.
```

Expected FableCodex behavior: use the ledger only when it is worth the overhead, keep findings separate from goals, require the findings gate before final completion, and summarize evidence in a final-response-ready form.

Verification evidence to collect: goal checkpoints, findings gate output, final verification command, and `codex-fable5 goals summary`.

## Release Dogfood Gate

When to use it: preparing a release where workflow behavior matters as much as unit-test coverage.

Prompt template:

```text
@codex-fable5 Dogfood this release before tagging.
Run one multi-step task with a goal ledger, one review-only task with findings gate discipline, and one debugging task with reproduce-first hypotheses.
Record prompts, environment, ledger/findings state, verification evidence, and friction points in docs/DOGFOOD_REPORT.md.
```

Expected FableCodex behavior: verify the local skill can be invoked, create ignored local ledgers for dogfood state, convert actionable friction into docs or issues, resolve accepted findings before release, and keep the committed report concise enough to review.

Verification evidence to collect: local smoke output, `codex-fable5 goals summary`, `codex-fable5 findings gate`, focused test output, and the normal release verifier.
