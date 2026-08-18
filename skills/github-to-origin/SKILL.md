---
name: github-to-origin
description: Agent runbook for moving a repository from GitHub to Cursor Origin code hosting, including repointing Vercel so production keeps deploying. The agent executes every step itself and verifies each one. Use when the user wants to move, migrate, or switch a repo to Origin, mentions Cursor Origin hosting, says "move to origin", or asks why pushes to Origin are not deploying.
---

# GitHub to Origin

You are the agent. The user says "move this repo to Origin" and you do the rest:
run the commands, verify every step with another command, and report what you
proved, not what you assume. Ask the user only for the inputs below and at the
two moments where a human is unavoidable.

The code move is the easy half. The half that breaks things is Vercel: a repo
can be on Origin while production still builds from GitHub, so pushes appear to
succeed and the live site silently stops updating.

## Two traps that look like success

1. **Syncing is not moving.** Connecting GitHub to Cursor creates a mirror.
   Pushes keep going to GitHub, which stays the source of truth. A synced repo
   shows `Mirror status: inbound` in `origin repo view`. Mirrors even accept
   pushes, so a successful push proves nothing about who is authoritative.
2. **Installing the Vercel app on the Origin repo is not deploying from it.**
   The existing Vercel project that owns the production domain keeps GitHub as
   its Git source until someone repoints it. Two separate connections; only one
   owns the domain.

## Inputs to collect before starting

- Origin org and repo name, e.g. `acme/site`. If the user is unsure, run
  `origin repo list` and show them the candidates.
- The production domain, e.g. `www.acme.com`. You will use it to find the right
  Vercel project, so do not guess it.
- Whether GitHub should be kept as a backup remote. Default yes.

## Human moments, stated upfront

1. `origin auth login` opens a browser the user must complete.
2. The Cursor-side detach (step 6) is a web UI with a type-to-confirm dialog and
   has no CLI. Drive the browser yourself if you have browser control;
   otherwise give the user the exact clicks and wait.

Everything else is yours. Do not hand the user a command you can run yourself.

## 0. Preflight

```bash
origin --version   # Origin CLI installed?
vercel --version   # Vercel CLI installed?
git status --porcelain
```

Origin needs a paid Cursor plan and is early beta. Uncommitted work in the tree
is fine, but never commit it as part of the migration.

## 1. Snapshot

Capture what correct looks like so the migration can be proved later:

```bash
git branch --format='%(refname:short)' | wc -l
git rev-list --count main
git rev-parse main
git rev-list --max-parents=0 HEAD
git tag | wc -l
```

## 2. Authenticate

Run `origin auth login` in the background and let it live until it exits on its
own. Never wrap it in a timeout and never kill it: killing invalidates the
challenge and no token is stored, even if the user completed the browser step.

Verify, do not assume:

```bash
origin auth status   # expect: Token: valid
```

Login also installs a git credential helper for `origin.cursor.com`, so no
further git auth setup is needed.

## 3. Find or create the Origin repo

```bash
origin repo view <org>/<repo>
```

- `Mirror status: inbound` means synced mirror. Continue; step 6 converts it.
- No mirror line means it is already a native Origin repo.
- Missing entirely: `origin repo create <org>/<repo>`.

## 4. Push everything

Add Origin under a temporary name so the existing `origin` remote stays
untouched until the push is proved:

```bash
git remote add cursor https://origin.cursor.com/<org>/<repo>.git
git fetch cursor
git push --dry-run cursor main   # proves writes are accepted
git push cursor --all
git tag | grep -q . && git push cursor --tags
```

## 5. Verify parity, then repoint remotes

```bash
git fetch cursor --prune
for b in $(git branch --format='%(refname:short)'); do
  git rev-parse --verify -q "cursor/$b" >/dev/null || echo "MISSING: $b"
done
git rev-parse main cursor/main   # must print the same sha twice
```

Only when nothing is missing:

```bash
git remote rename origin github
git remote rename cursor origin
git branch --set-upstream-to=origin/main main
```

Keeping GitHub as a named remote is what makes the migration reversible.

## 6. Detach from GitHub on the Cursor side

Until this is done, GitHub is still the source of truth.

At `cursor.com/codebase/<org>/<repo>`: **Settings** > **General** >
**Danger Zone** > **Detach from GitHub**, then type `<org>/<repo>` in the
confirm dialog. The dialog states the GitHub repo is not deleted.

Verify from the terminal:

```bash
origin repo view <org>/<repo>   # the Mirror status line must be gone
```

## 7. Repoint Vercel at Origin

This is the step that decides whether production updates.

**Trap: do not let the CLI auto-link.** `vercel ls` and `vercel link` in an
unlinked directory silently link by directory name, which can pick a similarly
named project that does not own the domain. Find the real project through the
domain instead:

```bash
vercel inspect https://<production-domain>
# read the "name" field: that project owns the domain
rm -rf .vercel
vercel link --yes --project <that-name>
```

Then repoint the Git connection:

```bash
vercel git disconnect
vercel git connect https://origin.cursor.com/<org>/<repo>.git
```

Both subcommands exist (verified on Vercel CLI 46.1.0). The docs only promise
"a Git provider repository" and never name Origin, so if `connect` rejects the
URL, fall back to the dashboard: **Project Settings** > **Git** >
**Connected Git Repository** > **Disconnect**, then connect the Origin repo.

Always repoint the existing project. Never let the Origin Vercel app create a
fresh project: the existing one holds the production domain, the environment
variables, and the deployment history, and a new one starts with none of them.

## 8. Prove the deploy, headlessly

```bash
vercel ls   # note the newest Production deployment URL
```

Push a real commit to `origin`, then poll:

```bash
vercel ls   # until a NEW Production deployment appears with status Ready
vercel inspect https://<production-domain>
# its "url" must equal the new deployment; "created" must be minutes ago
```

Do not verify by grepping the served HTML for markup you changed. Props passed
from server components to client components do not reliably appear in the HTML,
so that check reports failure for deploys that shipped fine. The CLI is the
authority on which deployment is live.

Finish with a health sweep:

```bash
for p in / <key routes>; do
  curl -s -o /dev/null -w "%{http_code} $p\n" "https://<production-domain>$p"
done
```

## 9. CI stops. Say so out loud.

GitHub Actions only run on GitHub. After the cutover, every workflow in
`.github/workflows/` stops firing, and nothing fails because nothing runs.
Origin runs existing workflows through Depot or Buildkite, connected from the
repo's **Apps** tab. Until one is connected, the only gate is whatever local
git hooks exist on the developer's machine. Tell the user this explicitly and
offer to set a replacement up.

## 10. Aftermath

- GitHub now drifts behind. Make it a decision, not an accident: either push
  there occasionally as a backup mirror or declare it intentionally stale.
  Public links and profile READMEs may still point at it.
- Rollback: rename the remotes back and reconnect Vercel to the GitHub repo.
  Nothing in this runbook deletes anything on GitHub.

## Checklist to report to the user

```
[ ] snapshot taken: branches, commits, head, root
[ ] origin auth status: Token valid
[ ] every branch verified present on Origin
[ ] remotes: origin -> Origin, github -> GitHub backup
[ ] detached: Mirror status line gone
[ ] Vercel project found via the domain, not auto-link
[ ] vercel git disconnect + connect done (or dashboard fallback)
[ ] new deployment proved live via vercel inspect
[ ] key routes return 200
[ ] user told CI is dark, replacement offered
```
