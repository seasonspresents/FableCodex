# Security And Privacy Review

Review date: 2026-07-08

Scope: v0.6 release readiness for the Codex plugin package, local helper scripts, docs, release tooling, provider bridge examples, and `.codex-fable5/` local state.

## Findings Closed

- Provider bridge docs used a real-looking Anthropic-style key placeholder. Replaced it with a neutral placeholder so docs remain copyable without normalizing fake secrets.
- `codex-fable5 update --ref` accepted option-like ref values. The wrapper now rejects ref values beginning with `-` before passing them to git.

## Reviewed Boundaries

- Secret exposure: docs, examples, and generated LiteLLM config use placeholders or `os.environ/ANTHROPIC_API_KEY`; no real key material should be committed. `SECURITY.md` and `CONTRIBUTING.md` call out API keys, provider tokens, and local ledgers.
- Provider routing: the provider bridge is optional, source-backed, and explicit that the repo does not provide model access. It recommends user-level Codex config for credentials and keeps project examples credential-free.
- Local state privacy: `.codex-fable5/` stores local goals, findings, and JSONL event evidence. It can contain task text, file paths, or snippets the user chose to record, so it is gitignored and should be treated as local-private working state.
- State recovery: `codex-fable5 doctor` summarizes local state and archive hints, but it does not print full ledger contents, delete ledgers, rewrite user state, or repair corrupted files automatically.
- Update behavior: `codex-fable5 update` only changes a git checkout of FableCodex, refuses dirty worktrees, fetches tags explicitly, ignores prerelease tags for the default stable update path, and now rejects option-like refs.
- Unsafe deletes: package scripts do not remove user state. The runtime smoke test deletes only its own temporary `CODEX_HOME` created with `mkdtemp`, unless `--keep-home` is supplied.
- Network calls: release verification is offline by default. Upstream source fetching only happens with `--source-check optional|required`; CI fetches a raw GitHub URL pinned to a 40-character commit SHA and does not send an Authorization header.
- Path handling: manifest tests keep packaged plugin paths inside the repository. The LiteLLM generator writes only to the user-specified output path and does not embed credentials.

## Residual Risks

- Users may record sensitive prompt text in goals or findings evidence. Treat `.codex-fable5/` as local-private state and do not paste secrets into ledger entries.
- Provider gateways are user-operated infrastructure. FableCodex can provide configuration shape and safety warnings, but cannot verify account-level model access, gateway auth policy, or provider retention behavior.
- `codex-fable5 update --ref main` follows the checkout's configured git remote. Users should only run update from a trusted checkout.

## Release Gate

Before v0.6 release, run:

```bash
python3 tools/verify_release.py --source-check required
python3 tools/codex_plugin_smoke.py --case all
```

Also confirm:

- `git status --short` does not include `.codex-fable5/`, generated build output, local provider configs, or secrets.
- Provider docs still use placeholders, not real-looking API key strings.
- Security and privacy review notes remain linked from `SECURITY.md` and the release checklist.
