---
name: ship-check
description: Proves a point-and-click adventure change in the builds people actually play, not the editor. Runs the headless import, GUT tests and content lint, exports the desktop and web builds, plays scripted QA scenarios in the exported app and in Chrome, checks what really shipped in the pack, measures per-room frame time, video memory and load time against budgets, records reels, files evidence in docs/qa, and deploys the web build to Vercel. Use when a slice is finished, before a commit or deploy, when the user says "test it", "does it work in the browser", "ship it", "deploy", "record a reel", "check performance", "why is the pack so big", when a QA scenario fails or times out, when a browser build freezes, hangs on a line or loses saves, or when prod shows a 404 after a push.
---

# ship-check

A feature is done when it works in the exported desktop build and in the web
build served locally, not when it works in the editor. Every check here runs
the real exports, prints PASS or FAIL lines, and leaves evidence in
`docs/qa/<plan>/`.

Read [RULES.md](RULES.md) for why each step exists. Commands are in
[WORKFLOW.md](WORKFLOW.md). The scenario list is in
[references/qa-scenarios.md](references/qa-scenarios.md), and the budgets in
[references/budgets.md](references/budgets.md).

## The loop

```
tools/test.sh  ->  export macos  ->  --qa=<scenario> in the app  ->  export web  ->  serve  ->  browser-qa
      ^                                                                                              |
      |                     fix in code or content, never by loosening a budget                       |
      +------------------  pack check  <-  room budgets  <-  reel  <-  docs/qa/<plan>/  <-------------+
                                                                              |
                                                                     deploy.sh [--prod]
```

1. **Tests.** `tools/test.sh`: headless import (fails on any script or import
   error), GUT, and the content lint. Logs in `build/test-logs/`.
2. **Desktop.** `tools/build/export.sh macos`, then run the exported app with
   `-- --qa=<scenario> --qa-out=<dir>`. The `Qa` autoload plays the scenario,
   saves screenshots, prints `[qa] PASS|FAIL` lines and a final
   `[qa] RESULT`, and quits with exit code 0 or 1.
3. **Browser.** `tools/build/export.sh web`, `bun tools/build/serve.ts`, then
   `bun tools/build/browser-qa.ts <scenario>`: a visible Chrome window with
   backgrounding off, `?qa=<scenario>` in the URL, two passes (cold and warm).
4. **Pack.** `export.sh` lists the real pack with `tools/build/pck_list.py` and
   fails if a part left out of the web build is still in it. Run
   `python3 tools/build/pck_list.py build/web/index.pck --sizes` to see what
   takes the space.
5. **Budgets.** `--qa=rooms --part=<id>` tours every room: load time, frame
   p95, video memory with both eras and every character loaded. It fails
   past 400 MiB, 1 s or 16.7 ms.
6. **Reels.** `--write-movie` with a temporary 1920×1080 `override.cfg`.
7. **Evidence.** Screenshots, `[qa]` lines, measurements and reels in
   `docs/qa/<plan>/`, with a README table of checks and results.
8. **Deploy.** `tools/build/deploy.sh` for a preview, `--prod` for production,
   then `browser-qa.ts` again against the deployed URL.

## Quick start

```sh
tools/test.sh
tools/build/export.sh macos
build/macos/<Game>.app/Contents/MacOS/<Game> -- --qa=greybox --qa-out=$PWD/docs/qa/<plan>/greybox
tools/build/export.sh web
bun tools/build/serve.ts &                       # http://localhost:8060/
bun tools/build/browser-qa.ts greybox
QA_BASE_URL=https://<project>.vercel.app bun tools/build/browser-qa.ts greybox   # after deploy
```

## Per-slice checklist

1. `tools/test.sh` ends with `== ALL PASSED`.
2. The slice's own scenario passes in the exported desktop app.
3. The same scenario passes in Chrome on the web export, both passes.
4. If the slice added rooms or characters: the part's room tour passes, and
   its numbers go in the evidence.
5. The web pack is within its budget and holds nothing it should not.
6. Evidence and a one-line result are in `docs/qa/<plan>/README.md`, and the
   board has an entry.
7. After any deploy, the deployed URL passes `browser-qa.ts`.

## Do not

- Do not call a feature done from the editor or from GUT alone.
- Do not loosen a budget or a QA threshold to make a check pass. Fix the
  content, or record a decision.
- Do not judge frame times from a hidden or covered browser tab.
- Do not leave `override.cfg` in the project after recording.
- Do not deploy without exporting first; the export wipes `build/web`.
- Do not print or upload `.env` or `.env.local`.

Back to [the production map](../README.md). The next part starts with
[story-track](../story-track/SKILL.md).
