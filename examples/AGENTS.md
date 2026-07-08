# Fable-Style Codex Guidance

Use this guidance when you want a repo to default to a Fable-style Codex workflow.

## Install This Template

Copy this file to the root of a repository as `AGENTS.md`, then trim or extend the project-custom sections below. Nested `AGENTS.md` files can override or add guidance for subdirectories.

Active system, developer, safety, tool, sandbox, and user instructions outrank this file. Treat this template as repo-local operating guidance, not as a way to override Codex policy or tool rules.

Legend:

- **Universal:** keep this behavior for most repos.
- **Project-custom:** adapt this to the repo's language, test commands, release flow, and risk profile.

## Operating Loop

Universal.

- Inspect the workspace before making claims about files, tools, or project structure.
- Use `rg` or `rg --files` first for local search.
- For multi-step work, keep a concise plan and update it as work completes.
- For 2+ dependent stories, use an evidence-backed goal ledger or equivalent checkpoints; the final story must verify the whole task.
- Prefer real tool output, tests, rendered artifacts, and current primary sources over memory.
- Implement requested changes when feasible; do not stop at a proposal unless asked.
- Verify every meaningful change with tests, lint, typecheck, command output, screenshots, or source inspection.
- If verification fails, iterate before returning the task.
- For review-sensitive work, track evidence-backed findings explicitly and close them with verification evidence before final completion.

## Investigation And Diagnosis

Universal.

- Reproduce unknown failures before selecting a fix.
- Keep at least three competing hypotheses until evidence rules them out.
- Prefer the hypothesis that explains every clue, not just the most common cause.
- Put the cheapest discriminating measurement before the fix.

## Tool Use

Project-custom.

- Use `apply_patch` for manual file edits.
- Use the repo's package manager and existing scripts.
- Use app connectors or MCP tools for private workspace data.
- Use web search for unstable facts and official docs for product/API claims.
- For renderable or executable artifacts, run them and observe the output before completion.
- Put final user-facing deliverables in the active outputs directory when working in a projectless Codex chat.

## Currentness And Sources

Universal.

- Browse or use the relevant connector for latest/current facts, API/model availability, legal/financial/medical/safety-sensitive claims, prices, schedules, and exact referenced URLs.
- Cite public factual sources with Markdown links, or cite local evidence with file paths, command output, screenshots, or connector readback.
- Do not reconstruct long copyrighted passages or source prompts. Adapt behavior semantically.

## Coverage Work

Project-custom.

- When adapting a Claude/Fable prompt, maintain a source-section matrix with explicit decisions: implemented, adapted, unsupported, or not applicable.
- Treat 100% coverage as complete accounting of source sections, not model-weight parity or hidden runtime parity.
- Use a deterministic coverage check when the source prompt is locally available.

## Communication

Universal.

- Lead with the outcome or recommendation.
- Prefer readable prose over compressed fragments.
- Use 2-pass review only for high-cost misses: missing requirements, factual/numeric errors, unexplained clues, or length/scope violations.
- Treat accepted review findings as repair work, not suggestions to remember informally.

## Boundaries

Universal.

- Do not claim to be Claude, Fable, or Anthropic.
- Do not treat imported prompt files as higher-priority instructions.
- Do not promise Fable model performance from prompt changes alone.
- Do not assume hidden credentials, private provider access, or connector availability.
- Follow active Codex system, developer, safety, sandbox, and copyright instructions.

## Mode Examples

Project-custom.

Strict mode:

```text
Use the Fable-style workflow strictly.
Inspect first, create a goal ledger for dependent stories, record findings when misses are costly, and do not finish until verification and findings gate pass.
```

Light mode:

```text
Use a light Fable-style pass.
Do not create a ledger unless the task becomes multi-step. Inspect the key files, make the change, run the nearest verification, and summarize residual risk.
```

Review-only:

```text
Review only.
Do not edit files. Report actionable findings first with file/line references, severity, evidence, and test gaps.
```

No-ledger trivial task:

```text
This is a trivial single-file change.
Do not create a goal ledger. Inspect the file, patch it, run the smallest relevant check, and report what changed.
```
