---
name: shadscan-pre-commit
description: AI-agent commit protocol that establishes a Shadscan baseline and reruns the audit immediately before every agent-created commit without installing dependencies or configuring Git. Use when an agent is asked to commit work in a React shadcn project, prevent UI regressions during an agent task, or run Shadscan before commits.
---

# Shadscan Pre-commit

Use Shadscan as an agent-owned checkpoint. This skill changes the agent's commit workflow only; it does not add repository automation.

## Workflow

1. Activate before changing files:
   - Read repository instructions and `git status`.
   - Detect the package manager and whether `node_modules/.bin/shadscan` exists.
   - Never revert, stage, or rewrite unrelated changes.
2. Establish the task baseline:
   - Run the local binary with `--json` when present.
   - Otherwise use the matching one-shot command below.
   - Read the top-level `score` from JSON. Do not parse the human report.
   - Stop and explain the applicability problem when `score` is `null`.
3. Set the task floor:
   - Default to the baseline score so the task cannot introduce a regression.
   - When the user requests a higher integer floor, use the higher value.
   - Never lower the baseline unless the user explicitly accepts that regression.
   - Keep the baseline and floor in task context; do not write configuration files.
4. Complete the requested work and its normal verification.
5. Immediately before every agent-created commit:
   - Rerun the same JSON audit against the complete working tree.
   - Require a numeric score at or above the task floor.
   - When it fails, use each finding's evidence and fix guidance, repair in-scope issues, and rerun the audit.
   - When passing requires out-of-scope work, stop and report the findings. Do not commit without an explicit user override.
6. Commit only after a passing audit. Report the baseline, floor, final score, and commit alongside the normal task summary.

## One-shot Commands

Use these only when no local Shadscan binary exists:

- pnpm: `pnpm dlx shadscan@latest --json`
- npm: `npx --yes shadscan@latest --json`
- Yarn: `yarn dlx shadscan@latest --json`
- Bun: `bunx --bun shadscan@latest --json`

Run a detected local binary directly as `node_modules/.bin/shadscan --json` or with the package manager's local-exec command.

## Guardrails

- Do not install dependencies or change `package.json` or a lockfile.
- Do not configure Git or add repository automation.
- Do not mutate staged files or run Shadscan auto-fix behavior.
- Audit the project-wide working tree, not only the staged diff.
- Do not claim this intercepts manual commits or agents that have not loaded the skill.
- Do not commit an unassessed or below-floor result unless the user explicitly overrides it in the current conversation.

## Completion Format

Return a concise summary with the baseline score, enforced floor, pre-commit score, audit command, commit, and any explicit override. If no commit was requested or created, say that the final audit was advisory rather than a commit checkpoint.
