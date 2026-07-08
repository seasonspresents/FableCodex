# Releasing

This project uses a lightweight release process because it is a small Codex plugin package.

## Release Checklist

1. Confirm the working tree is clean before release edits.
2. Update `CHANGELOG.md`.
3. Update `plugins/codex-fable5/.codex-plugin/plugin.json` when the plugin version changes.
4. Confirm README installation and usage examples still match the packaged plugin.
5. Run local verification:

```bash
python3 tools/verify_release.py --source-check required
```

`--source-check required` fetches the README.md-pinned `elder-plinius/CL4R1T4S` `ANTHROPIC/CLAUDE-FABLE-5.md` from `https://raw.githubusercontent.com/elder-plinius/CL4R1T4S/${PIN}/ANTHROPIC/CLAUDE-FABLE-5.md`, writes it to `build/fable5/CLAUDE-FABLE-5.md`, and runs `fable_coverage.py --source build/fable5/CLAUDE-FABLE-5.md`. Use the default `python3 tools/verify_release.py` for offline local work where the upstream source check should be skipped.

If Codex is installed locally, also run:

```bash
python3 tools/codex_plugin_smoke.py --case all
```

6. Review `docs/SECURITY_PRIVACY_REVIEW.md` and `docs/DOGFOOD_REPORT.md`, then verify no secrets, `.codex-fable5/` ledgers, generated build output, local provider configs, or real-looking API key placeholders are staged.
7. Commit the release changes.
8. Tag the release with the plugin version, for example:

```bash
VERSION=$(python3 -c 'import json; print(json.load(open("plugins/codex-fable5/.codex-plugin/plugin.json"))["version"])')
git tag "v${VERSION}"
git push origin main "v${VERSION}"
```

9. Create a GitHub release that summarizes user-visible changes and links to the changelog.

## Versioning

Use semantic versioning for the plugin package:

- Patch: documentation fixes, test additions, small script fixes.
- Minor: new workflow guidance, new helper scripts, or new examples.
- Major: breaking plugin layout or behavior changes.

## Release Boundaries

Do not release changes that claim unavailable model access, include credentials, or copy protected prompt text into the repository.
