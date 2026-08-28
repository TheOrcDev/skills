---
name: grond
description: One word, GROND, and the agent stages everything, commits it, gets it onto the default branch, pushes, and reports every step in orc voice. Saying GROND is the authorization, so the agent never asks for confirmation. Use when the user says "GROND", "grond it", "smash it to main", or invokes /grond.
---

# GROND

The hammer of the underworld. The user says one word, **GROND**, and you take
every change in the working tree, put it on the default branch, and push it.
No plan, no confirmation prompt, no "are you sure". The word is the order.

**GROND is the authorization.** Committing and pushing to `main` is normally a
confirm-first action. Here the user has pre-authorized it by name, once, in
advance. Do not ask again. Do not offer a gentler alternative. Swing.

**But an orc is blunt, never wrong.** You report what actually happened. If the
gate holds, you say the gate holds. Never announce a push that did not land.

## The swing

Run these yourself, in order, verifying as you go.

### 1. Find the gate

```bash
git rev-parse --git-dir && git status --porcelain=v1 -b && git remote -v
```

- No repo: "No gate here, warchief." Stop.
- No remote: commit locally, push nothing, and say plainly that nothing left the
  machine.

### 2. Check the ram for poison

Look at what you are about to commit before you stage it:

```bash
git status --porcelain -uall
```

Halt if that list holds secrets that do not belong in history: `.env` and its
variants (`.env.example` is fine), `*.pem`, `*.key`, `id_rsa`, `*.p12`,
`*credentials*.json`, service-account keys. Name the files and say GROND does
not smash secrets into a remote. If the user says GROND a second time after
seeing the list, that is their call. Proceed.

Everything else goes in. GROND does not curate.

### 3. Load everything

```bash
git add -A
```

### 4. One commit, real message

Read `git diff --cached --stat` and the diff itself, then write a message that
describes the actual change. Imperative, one line, no em dashes, and no "GROND"
in it. The chant belongs in the chat, not in the log.

```bash
git commit -m "<message>"
```

Nothing staged and nothing ahead of the remote: "Gate already down." Skip to the
report.

### 5. Get it onto the default branch

Find the real default branch name, do not assume `main`:

```bash
MAIN=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
[ -n "$MAIN" ] || MAIN=$(git remote show origin | sed -n 's/.*HEAD branch: //p')
echo "$MAIN"
```

Both lines matter. `origin/HEAD` is often unset on a fresh clone, and a failing
`symbolic-ref` piped into `sed` still exits 0, so a plain `||` fallback would
never run and you would push to an empty branch name.

Read the name off `echo`, then substitute it literally for `main` in every
command below. Do not rely on `$MAIN` surviving into a later shell.

- **Already on it:** go to step 6.
- **On another branch:** check out the default branch and merge yours into it.
  Keep the branch, do not delete it.

```bash
git checkout main && git merge <branch>
```

- **Conflict:** run `git merge --abort`, return with `git checkout <branch>`, and
  report the conflicting files. Do not resolve someone's conflicts under a
  one-word order. The tree goes back exactly where it started.
- **Detached HEAD:** say so and stop. Do not guess which branch was meant.

### 6. Push

```bash
git push origin main
```

Rejected because the remote moved ahead, one retry only:

```bash
git pull --rebase origin main && git push origin main
```

If it fails again, stop and quote the remote's own error text verbatim.

**Never `--force`, never `--force-with-lease`, never rewrite pushed history.**
GROND smashes forward through the gate. It does not smash the warband behind it.

Rejected by a branch protection rule: that gate is stronger than the ram. Name
the rule, report it, and offer the PR route. Do not try to route around it.

### 7. Prove the gate fell

```bash
git status -sb && git log --oneline -1 origin/main
```

Report the SHA that is actually on the remote. If local and `origin/main` do not
match, the push did not land, whatever the earlier output looked like.

## The report

Orc voice. Chant on top, facts underneath. Short lines, no hedging.

**Gate down:**

```
GROND. GROND. GROND.

Gate is down, warchief.
  Smashed: 7 files, 1 commit
  Message: "Add rate limiting to the auth endpoint"
  Landed:  main @ a3f9c21
Lok'tar.
```

**Gate held:**

```
GROND. GROND. GROND.

Gate holds, warchief. Ram bounced.
  Reason:  main is protected, direct pushes rejected
  Remote:  "GH006: Protected branch update failed"
  Local commit stands at a3f9c21. Nothing pushed.
Next swing: open a PR, or drop the protection.
```

Never dress a failure as a win. Code, paths, SHAs, and remote error text stay
verbatim. The orc voice is for the prose around them.

## Stand down

GROND is one swing, not a mode. After the report you return to your normal
voice, and nothing else is pushed until the user says the word again.
