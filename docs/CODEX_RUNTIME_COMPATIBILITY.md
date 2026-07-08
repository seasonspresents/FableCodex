# Codex Runtime Compatibility

This note records the Codex runtime behavior verified for the packaged
FableCodex marketplace and plugin manifests.

## Verified Runtime

- Codex CLI: `codex-cli 0.128.0`
- App-server user agent: `Codex Desktop/0.128.0 (Mac OS 15.7.5; arm64)`
- Verification date: 2026-07-08
- Plugin id observed by Codex: `codex-fable5@fablecodex`
- Skill name observed by Codex: `codex-fable5:codex-fable5`

## Marketplace Lifecycle

The marketplace can be added from a stable Git tag, from `main`, or from a local
checkout:

```bash
codex plugin marketplace add baskduf/FableCodex --ref v0.6.0
codex plugin marketplace add baskduf/FableCodex --ref main
codex plugin marketplace add /path/to/FableCodex
```

For Git-backed marketplaces, upgrade and remove are available:

```bash
codex plugin marketplace upgrade fablecodex
codex plugin marketplace remove fablecodex
```

Local marketplaces can be removed, but `upgrade` correctly fails because they
are not configured as Git marketplaces.

## Plugin Enablement

In `codex-cli 0.128.0`, the public CLI exposes marketplace management but does
not expose a `codex plugin add` subcommand. Plugin enablement is available via
the Codex app-server/Desktop plugin API:

- `plugin/list` shows `codex-fable5@fablecodex` as `installed:false` and
  `enabled:false` after marketplace add.
- `plugin/install` with `pluginName: "codex-fable5"` and the marketplace
  manifest path enables the plugin.
- After install, `plugin/list` reports `installed:true` and `enabled:true`.
- `skills/list` with `forceReload:true` reports `codex-fable5:codex-fable5`.

The install writes this config entry:

```toml
[plugins."codex-fable5@fablecodex"]
enabled = true
```

The older README command below is not valid for this runtime and should not be
documented as the current CLI enablement path:

```bash
codex plugin add codex-fable5@fablecodex
```

Observed error:

```text
error: unrecognized subcommand 'add'
```

## Manifest Field Decisions

The current runtime accepts and surfaces these fields from
`plugins/codex-fable5/.codex-plugin/plugin.json`:

- `name`
- `version`
- `description`
- `license`
- `skills`
- `interface.displayName`
- `interface.shortDescription`
- `interface.longDescription`
- `interface.developerName`
- `interface.category`
- `interface.capabilities`
- `interface.defaultPrompt`
- `interface.brandColor`

`interface.defaultPrompt` is treated as starter prompt metadata. Keep it to at
most three entries, and keep each prompt no longer than 128 characters.

The app-server response normalizes some omitted optional interface fields to
empty arrays or `null`, including `screenshots`, `screenshotUrls`, logo fields,
composer icon fields, website URL, privacy policy URL, and terms URL. The
package does not need to declare those fields unless they become useful.

## Local Test Boundary

CI should not require a local Codex binary. The repository tests enforce the
locally checkable runtime contract: manifest shape, policy enums, prompt limits,
skill path resolution, category/capability metadata, color format, and this
compatibility note.

## Fresh Install Smoke

Maintainers with a local Codex install can run the full runtime smoke:

```bash
python3 tools/codex_plugin_smoke.py --case all
```

The smoke creates a temporary `CODEX_HOME` for each install path and verifies:

- `codex plugin marketplace add` for local checkout, stable tag, and `main`.
- app-server `plugin/install` changes `codex-fable5@fablecodex` from
  `installed:false` / `enabled:false` to `installed:true` / `enabled:true`.
- app-server `skills/list` with `forceReload:true` exposes
  `codex-fable5:codex-fable5`.
- `codex debug prompt-input '@codex-fable5 Say hello'` includes the enabled
  plugin and skill in model-visible context.
- The installed package wrapper runs from its package path with
  `codex-fable5 version`.
- `plugin/uninstall` disables the plugin again.
- Git-backed marketplaces support `codex plugin marketplace upgrade`.
- All marketplace cases support `codex plugin marketplace remove`.

Use `--case local`, `--case stable`, or `--case main` to narrow the run. Use
`--keep-home` to inspect the temporary `CODEX_HOME` after a smoke run.
