# State Recovery

FableCodex stores local task state in `.codex-fable5/`. These files are working ledgers, not source files, and `.codex-fable5/` should stay ignored by git.

Run the safe diagnostic first:

```bash
codex-fable5 doctor
```

The doctor identifies state files and prints archive-first hints. It does not delete, rewrite, or repair user ledgers automatically.

## Corrupted `goals.json`

Symptoms:

- `codex-fable5 goals status` reports invalid JSON or an invalid `goals` schema.
- `codex-fable5 doctor` prints `FAIL state` for `.codex-fable5/goals.json`.

Recovery:

1. Archive the file before changing anything:

```bash
mv .codex-fable5/goals.json .codex-fable5/goals.json.broken.<timestamp>
```

2. Recreate the plan from the latest reliable context:

```bash
codex-fable5 goals create --brief "<brief>" --goal "inspect::<objective>"
```

3. Keep the archived file until you have copied out any evidence you still need.

## Corrupted `findings.json`

Symptoms:

- `codex-fable5 findings status` reports invalid JSON or an invalid `findings` schema.
- Final goal checkpoints fail because the findings ledger cannot be read.

Recovery:

1. Archive the file:

```bash
mv .codex-fable5/findings.json .codex-fable5/findings.json.broken.<timestamp>
```

2. Recreate any still-actionable findings:

```bash
codex-fable5 findings add --title "<title>" --evidence "<evidence>"
```

3. Run the gate before final completion:

```bash
codex-fable5 findings gate
```

## Stale Locks

On platforms without `fcntl`, FableCodex uses `.codex-fable5/state.lockdir` as a fallback lock. If a process is interrupted, the directory can remain.

Recovery:

1. Confirm no `codex-fable5` command is still running.
2. Archive the stale lock directory instead of deleting it immediately:

```bash
mv .codex-fable5/state.lockdir .codex-fable5/state.lockdir.stale.<timestamp>
```

3. Rerun the interrupted command.

## Interrupted Forced Plan Replacement

`codex-fable5 goals create --force` replaces the goal plan and archives the active findings ledger to `findings.<timestamp>.archive.json` after the new plan is safely written. If work is interrupted near that boundary, inspect the archive files before continuing.

Recovery:

1. Run `codex-fable5 doctor` and look for `state-archives` warnings.
2. Review every `.codex-fable5/findings.*.archive.json` file.
3. If an archive contains findings that still matter, restore it by copying it back to `.codex-fable5/findings.json` or recreate the actionable findings with `codex-fable5 findings add`.
4. Run `codex-fable5 findings gate` before final goal completion.

Do not commit recovered ledgers unless you intentionally want to preserve a task transcript.
