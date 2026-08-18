---
name: github-to-origin
description: Move a repository from GitHub to Cursor Origin code hosting, including making Vercel deploy from Origin instead of GitHub. Use when the user wants to move, migrate, or switch a repo to Origin, mentions Cursor Origin hosting, says "move to origin", or asks why pushes to Origin are not deploying.
---

# GitHub → Origin

Move a repo from GitHub to Cursor Origin and keep deployments working.

The code move is the easy half. The half that breaks things is Vercel: a repo can
be on Origin while production still builds from GitHub, so pushes appear to
succeed and the live site silently stops updating.

## The trap that makes this non-obvious

**Syncing is not moving.** Connecting GitHub to Cursor creates a *mirror*. Cursor's
own docs are explicit: pushes keep going to GitHub, which stays the source of
truth. A synced repo shows `Mirror status: inbound`.

**Installing the Vercel app on the Origin repo is not the same as deploying from
it.** The Vercel app can be installed on the Origin repo while the existing
Vercel *project* still has GitHub as its Git source. Two separate connections.
Only one owns the production domain.

Both look like success. Neither is.

## Before you start

- Origin is early beta and needs a paid Cursor plan.
- The `origin` CLI must be installed. Check with `origin --version`.
- Two steps need a human in a browser and cannot be automated: the login, and
  the detach confirmation. Plan for that rather than discovering it midway.

## 1. Snapshot first

Capture what "correct" looks like, so the migration can be *proven* rather than
assumed:

```bash
git branch --format='%(refname:short)' | wc -l   # branch count
git rev-list --count main                        # commit count
git rev-parse main                               # head
git rev-list --max-parents=0 HEAD                # root commit
```

## 2. Authenticate

```bash
origin auth login
```

This opens a browser and then **waits**. Do not run it with a timeout or kill
it — killing it invalidates the challenge and the token is never stored. Run it
in the background and let it complete, then confirm:

```bash
origin auth status    # expect: Token: valid
```

Login also configures a git credential helper for `origin.cursor.com`, so no
further git auth setup is needed.

## 3. Find or create the Origin repo

```bash
origin repo list                  # existing repos and clone URLs
origin repo view <org>/<repo>     # check Mirror status
```

- `Mirror status: inbound` → it is a **synced mirror**, not a move. Continue; the
  detach in step 6 is what converts it.
- No mirror status → already a native Origin repo.

If it does not exist: `origin repo create <org>/<repo>`.

## 4. Push everything

Add Origin under a temporary name so the existing `origin` remote (GitHub) is
untouched until the push is proven:

```bash
git remote add cursor https://origin.cursor.com/<org>/<repo>.git
git fetch cursor
git push --dry-run cursor <some-branch>   # confirms writes are accepted
git push cursor --all
```

Mirrors do accept pushes, so a successful push does **not** prove the repo is
detached. Only step 6 does that.

Note `--all` pushes branches only. Add `git push cursor --tags` if the repo has
tags.

## 5. Verify parity, then repoint

Prove every branch arrived before changing any default:

```bash
git fetch cursor --prune
for b in $(git branch --format='%(refname:short)'); do
  git rev-parse --verify -q "cursor/$b" >/dev/null || echo "MISSING: $b"
done
git rev-parse main cursor/main    # must match
```

Then make Origin the default:

```bash
git remote rename origin github
git remote rename cursor origin
git branch --set-upstream-to=origin/main main
```

Keeping GitHub as a named remote is what makes the whole migration reversible.

## 6. Detach from GitHub (browser, human required)

Until this is done GitHub is still the source of truth.

`cursor.com/codebase/<org>/<repo>` → **Settings** → **General** → **Danger Zone**
→ **Detach from GitHub** → type `<org>/<repo>` to confirm.

The dialog states the GitHub repo is **not deleted**. After detaching, the Sync
Status panel and the detach option disappear, and `origin repo view` no longer
reports a mirror status. Verify that rather than trusting the click.

## 7. Point Vercel at Origin (browser, human required)

**This is the step that decides whether production updates.**

In the Vercel **project** that owns the production domain:

**Project Settings** → **Git** → **Connected Git Repository** → **Disconnect**,
then connect the Origin repo.

Repoint the existing project rather than letting the Origin Vercel app create a
new one. The existing project already holds the production domain, the
environment variables and the deployment history; a new project starts with none
of them and needs the domain moved across, which means downtime.

Confirm the panel then reads the Origin repo with the Origin icon, not GitHub.

## 8. Verify the deploy — from the dashboard

Push a real commit, then check the Vercel project overview:

```
Source   main · <sha>  <commit message>
```

It must show the sha you just pushed, and the deploy author/icon should be
Origin rather than GitHub.

**Do not try to verify by grepping the deployed HTML for something you changed.**
Server-component props passed to client components do not reliably appear in the
served markup, so a grep can report "not deployed" for a deploy that shipped
fine. The dashboard is the only thing that knows which commit is live.

## 9. CI stops — decide what replaces it

GitHub Actions only run on GitHub. Once pushes go to Origin, every workflow in
`.github/workflows/` stops firing, silently.

Origin runs existing workflows through **Depot** or **Buildkite**, connected from
the repo's **Apps** tab. Until one is connected there are no server-side checks.
A local pre-push hook still runs, but only on the machine that has it.

Say this out loud to the user. Losing CI is easy to not notice, because nothing
fails — nothing runs.

## 10. Afterwards

- GitHub stays behind and drifts. Decide deliberately: occasional backup mirror,
  or intentionally stale. Profile READMEs and public links may still point there.
- Rollback is `git remote rename` in reverse plus reconnecting Vercel to GitHub.
  Nothing in this process deletes anything on GitHub.

## Checklist

```
[ ] snapshot: branches, commits, head, root
[ ] origin auth status → Token: valid
[ ] all branches pushed and verified present on Origin
[ ] remotes: origin → Origin, github → GitHub
[ ] detached: no Mirror status, Sync panel gone
[ ] Vercel project Git source = Origin repo
[ ] test push → dashboard shows that sha live
[ ] CI replacement connected, or user told it is gone
```
