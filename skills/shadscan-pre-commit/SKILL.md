---
name: shadscan-pre-commit
description: Configures a repository to run a version-pinned Shadscan audit before every commit without overwriting existing hooks. Use when a user asks to add Shadscan as a pre-commit gate, prevent shadcn UI regressions, or wire Shadscan into Husky, Lefthook, or simple-git-hooks.
---

# Shadscan Pre-commit

Add a deterministic Shadscan score gate to a JavaScript or TypeScript repository. Preserve the project's package manager, scripts, hooks, lockfile, and unrelated working-tree changes.

## Workflow

1. Inspect before editing:
   - Read `package.json`, its `packageManager` field, and lockfiles.
   - Read existing hook configuration, including `.husky/`, `lefthook.yml`, `lefthook.yaml`, and `simple-git-hooks` in `package.json`.
   - Check `git status`; never revert, stage, or rewrite unrelated changes.
   - Detect whether `shadscan` is already installed locally.
2. Establish a baseline:
   - Use the local binary when present: `<package-manager> exec shadscan --json`.
   - Otherwise run a one-time package-manager equivalent of `npx --yes shadscan@latest --json`.
   - Read the top-level `score`; do not parse the human report.
   - Use a user-specified integer threshold from 0 to 100 when provided. Otherwise use the current score so adoption prevents regressions immediately.
   - If a gate already exists, preserve its threshold unless the user explicitly requests a change. Never replace it with a lower baseline.
   - Stop and explain the applicability problem when the score is `null`. Do not invent a threshold.
3. Install a reproducible local gate:
   - Add `shadscan` as a dev dependency with the detected package manager.
   - Keep the resolved version in the lockfile. Do not put `dlx`, `npx`, `bunx`, or another network-dependent installer in the Git hook.
   - Add or preserve this package script: `"audit:ui": "shadscan --fail-under <threshold> --no-roast"`.
4. Reuse the existing hook manager. If none exists, install Husky as a dev dependency and run its current `init` command for the detected package manager.
5. Append the package-manager equivalent of `npm run audit:ui` to the existing pre-commit hook. Preserve every existing command and configuration key.
6. Verify:
   - Run the new `audit:ui` script directly.
   - Confirm a passing score exits zero.
   - When the baseline is below 100, run a one-off audit with `--fail-under <baseline + 1>` to confirm a failing score exits nonzero. Do not edit the configured script for this test.
   - At a baseline of 100, skip the synthetic failure because no valid higher threshold exists and report that limitation.
   - Re-read the hook and `package.json`; report changed files, pinned Shadscan version, baseline, threshold, and hook manager.

## Hook Managers

- **Husky:** put the detected package-manager run command on its own line in `.husky/pre-commit`. Preserve the file and executable mode. Never replace an existing hook.
- **Lefthook:** add a uniquely named `shadscan` command under `pre-commit.commands` with `run: <package-manager> run audit:ui`. Preserve other commands and YAML structure.
- **simple-git-hooks:** merge `"pre-commit": "<existing command> && <package-manager> run audit:ui"` into its existing object. Do not discard the existing command.
- **Unknown or custom manager:** inspect its documentation or local configuration before editing. Do not silently install a second manager.

## Guardrails

- Audit the working tree as it exists at commit time; Shadscan is project-wide, not staged-file-only.
- Do not run auto-fixers from this hook and do not mutate staged files.
- Do not lower an existing threshold unless the user explicitly asks.
- Do not duplicate the Shadscan command when the hook is already configured.
- Do not use raw `.git/hooks` for shared setup because those files are not versioned.
- Mention `git commit --no-verify` only as an emergency bypass; do not use it during verification.
- If dependency installation is unavailable, leave the repository consistent and report the exact blocker.

## Completion Format

Return a concise summary with the baseline score, enforced threshold, hook manager, package script, verification result, and files changed. Call out that teammates must install dependencies once after pulling the configuration.
