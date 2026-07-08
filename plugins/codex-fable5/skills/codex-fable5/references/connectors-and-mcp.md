# Connectors And MCP

Use this reference when adapting Fable-style MCP app suggestions, connector discovery, or third-party tool routing.

## Routing Order

1. Use installed app/plugin capabilities already exposed in the current Codex session.
2. Use `tool_search` when the user asks for a tool-backed action and the tool is not already loaded.
3. Use connector readback for private workspace data instead of public web search.
4. Use plugin install flow only when the user explicitly asks for a specific plugin/connector that is not available.
5. Fall back to public web only when the needed data is public/current and no private connector is required.

## Direct Connector Calls

Call an app/MCP tool directly when:

- The user names that app or gives an app URL/object.
- The data/action lives in the app, such as a GitHub PR, Google Drive file, Figma canvas, Notion page, or Canva design.
- The active tool schema supports the exact read/write operation needed.

Read the relevant skill first when a plugin skill says it is mandatory for the operation.

## Practical Routing Examples

### GitHub And Repo Objects

Use local repo tools first for files, branches, diffs, tests, and commits that are already in the workspace. Use GitHub, GitHub CLI, or a GitHub MCP/app connector when the user asks about remote-only objects such as pull requests, issue comments, checks, code scanning alerts, release metadata, or private repository state.

Example prompt:

```text
@codex-fable5 Review the GitHub PR linked in this issue and verify the local patch still matches it.
```

Routing:

- Read local files with normal filesystem/git tools when the repo is cloned.
- Use connector readback for PR discussion, review comments, CI/check status, private issues, or advisory data.
- Use public web search only for public GitHub pages when no private connector data is needed.

### Browser And Chrome Visual Verification

Use the in-app Browser for local app previews, public pages, screenshots, console checks, and performance traces that do not need the user's signed-in Chrome profile. Use Chrome when the task depends on a signed-in website, browser profile, extension state, or a site that only works in the user's Chrome session.

Example prompt:

```text
@codex-fable5 Verify this checkout flow visually.
Use Browser for the local preview unless a signed-in Chrome session is required.
```

Routing:

- If Browser/Chrome tools are not already loaded, use `tool_search` for the requested browser capability before assuming it exists.
- Capture visible evidence: screenshot, console status, network/performance trace, or viewport notes.
- Do not treat code inspection as a substitute for rendered verification when the user asked for visual behavior.

### Linear Issue And Project Work

Use Linear tools when the user names a Linear issue/project, asks for issue creation or updates, or wants status/priority/label/project work in Linear.

Example prompt:

```text
@codex-fable5 Turn this implementation plan into Linear issues under the Personal team.
Read existing project context first, then create or update issues with acceptance criteria.
```

Routing:

- Read before write: list teams/projects/statuses/issues, then create comments/issues/updates.
- Preserve Linear identifiers such as `PER-123` in evidence and final summaries.
- Avoid hard-coding private workspace names unless the user gave them or connector readback confirms them.

### Documents, Spreadsheets, And PDFs

Use document/spreadsheet/PDF connectors or bundled document skills when the user references private files, uploaded files, Drive/Docs/Sheets objects, or local PDFs. Public web search is not a substitute for reading the actual private document.

Example prompt:

```text
@codex-fable5 Extract the acceptance criteria from this product spec and turn them into implementation tasks.
Use connector readback for the source document and cite the document sections you used.
```

Routing:

- Use connector readback or local file parsing for the source artifact.
- Preserve document/sheet/page references in evidence.
- Use public web only for external facts needed to interpret the document, and label those sources separately.

## Connector Readback Versus Public Web Search

Use connector readback when the source is private, user-owned, permissioned, mutable inside an app, or referenced by an app URL/object ID. Use public web search when the needed fact is public, current, and not specific to the user's private workspace.

When both are needed, read the private connector source first, then use public/current sources only for external claims. Keep the provenance separate in the final response.

## Tool Discovery Pattern

- If the tool is already visible in the active tool list, call it directly.
- If the user asks for a specific app/plugin/connector and the tool is not loaded, use `tool_search` before saying it is unavailable.
- If `tool_search` finds a relevant tool, follow that tool's schema and any associated skill instructions.
- If no tool is available, explain the gap and choose the safest fallback. Do not fabricate tool names, connector IDs, or readback results.

## Opt-In And Installation

- Do not imply a connector is installed until the active tool list or `tool_search` proves it.
- Do not request plugin install for adjacent capabilities or broad recommendations.
- If a requested connector is missing and no install flow is available, explain the gap and use the best safe fallback.
- Do not fabricate marketplace results, app IDs, credentials, or tool output.

## What To Avoid

- Do not browse public web for private workspace data that should come from a connector.
- Do not ask the user to manually export app data before trying the available connector.
- Do not convert every task into an app suggestion; use connectors only when they materially help.
- Do not preserve Claude-specific connector names or policies as active instructions.

## Expected Feel

Connector routing should be quiet and practical: use the tool, verify the result, and report the outcome. Mention routing details only when they affect setup, permissions, evidence, or a limitation.

## Official Codex Sources To Recheck

- MCP and integrations overview: `https://developers.openai.com/codex/mcp`
- Browser use: `https://developers.openai.com/codex/app/browser-use`
- Chrome extension: `https://developers.openai.com/codex/app/chrome-extension`
- Linear integration and local MCP: `https://developers.openai.com/codex/integrations/linear`
- GitHub integration: `https://developers.openai.com/codex/integrations/github`
