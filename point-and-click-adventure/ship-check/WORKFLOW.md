# ship-check workflow

Run from the repository root. `<Game>` is the export name in
`export_presets.cfg` (the macOS preset's `export_path`), `<plan>` the plan
being executed, `<project>` the Vercel project.

## 0. Environment

| Variable | Default | Used by |
|---|---|---|
| `GODOT_BIN` | `$HOME/Applications/Godot-4.7.2.app/Contents/MacOS/Godot` | `tools/godot.sh` and everything that calls Godot |
| `QA_BASE_URL` | `http://localhost:8060/` | `browser-qa.ts`, to point it at a deployed build |

Export templates for 4.7.2 must be installed in Godot. Chrome must be at
`/Applications/Google Chrome.app`. `jq` is used by `export.sh`.

## 1. Tests and lint

```sh
tools/test.sh
# == import   (fails on SCRIPT ERROR or ^ERROR in build/test-logs/import.log)
# == tests    (GUT over res://test, with test/hooks/pre_run.gd)
# == lint     (addons/adv_tools/lint.gd)
# == ALL PASSED
```

Tool tests, when their tools changed:

```sh
(cd tools/images && bun test)
(cd tools/audio && bun test)
(cd tools/art && uv run pytest)
```

## 2. Desktop build and QA

```sh
tools/build/export.sh macos            # build/macos/<Game>.app; fails on export errors
out=$PWD/docs/qa/<plan>/<scenario>
build/macos/<Game>.app/Contents/MacOS/<Game> -- --qa=<scenario> --qa-out=$out
echo $?                                # 0 on PASS
```

Output: `[qa] at <step>`, `[qa] PASS <what>`, `[qa] FAIL <what>`, and last
`[qa] RESULT PASS` or `[qa] RESULT FAIL <failures>`. A timeout reads
`timed out at <step>`.

Useful flags after `--`:

| Flag | Does |
|---|---|
| `--qa=<scenario>` | Runs a scenario (see [references/qa-scenarios.md](references/qa-scenarios.md)) |
| `--qa-out=<absolute dir>` | Where screenshots go (default `user://qa`) |
| `--rooms=a,b` | The `rooms` tour on these rooms |
| `--part=<id>` | The `rooms` tour on a part's rooms, with its story flags preset from `content/chapters.json` |
| `--uncapped` | `perf` with vsync off, so frame times show the real cost |
| `--force-draw` | Draw every frame even when the window is covered (movies) |

The export command takes `release` (default) or `debug` as a second argument.
`export.sh` covers `macos` and `web`; add a target per preset for Windows and
Linux.

## 3. Web build and browser QA

```sh
tools/build/export.sh web              # build/web/index.html + index.pck; checks the pack
bun tools/build/serve.ts               # http://localhost:8060/ (port as first arg)
```

In another terminal:

```sh
bun tools/build/browser-qa.ts <scenario> [canvas=1920x1080] [passes=2] [shots-dir]
# [browser] {"hidden":false,"dpr":2}
# [pass 1] [qa] PASS ...
# [pass 2] [qa] RESULT PASS
```

- It prints the game's `[qa]` lines, console errors, uncaught exceptions and
  page crashes, and exits 0 only if every pass passed.
- With a `shots-dir`, each screenshot the scenario takes is also captured from
  the page (the game's own land in the browser's storage).
- Quote the warm pass.
- `[browser] Chrome's debugging endpoint did not come up` inside an agent's
  sandboxed shell usually means the sandbox refused Chrome's renderers
  (`bootstrap_look_up … Permission denied` on stderr). Run `browser-qa.ts`
  outside the sandbox; it only opens a throwaway profile on localhost.

A manual look through browser automation: open
`http://localhost:8060/?qa=<scenario>` (skips the click) or the plain URL
(click through the loading screen), and take bursts of small screenshots;
each one forces a frame in a hidden tab.

## 4. The pack

```sh
python3 tools/build/pck_list.py build/web/index.pck --sizes   # MB per top folder, total
python3 tools/build/pck_list.py build/web/index.pck | grep -v '^content/'   # anything odd
```

`export.sh web` already fails if a part not marked `"web": true` in
`content/chapters.json` is still in the pack. If the pack holds `build/`,
scratch images or raws, a folder is missing its `.gdignore`.

## 5. Room budgets

```sh
build/macos/<Game>.app/Contents/MacOS/<Game> -- --qa=rooms --part=<id> --qa-out=$PWD/docs/qa/<plan>/rooms
# [qa] ROOM {"room":"<id>","load_ms":..,"video_mib":..,"frames":{"p95_ms":..}}
# [qa] PASS <id> stays under 400 MiB of video memory (...)
# [qa] PASS <id> loads in under 1 s (...)
# [qa] PASS <id> holds 60 fps (frame p95 ... ms)
```

The tour also shoots each room in both eras and checks that every hotspot
answers Look. Copy the `ROOM` lines into the evidence table. Run it in Chrome
too for load time without threads (budget 2 s).

## 6. Reels

```sh
cat > override.cfg <<'EOF'
[display]
window/size/window_width_override=1920
window/size/window_height_override=1080
EOF
mkdir -p build/reels
tools/godot.sh --write-movie build/reels/<name>.avi --fixed-fps 30 -- --qa=<clip-scenario> --force-draw
rm override.cfg
ffmpeg -i build/reels/<name>.avi -c:v libx264 -crf 20 -pix_fmt yuv420p docs/qa/<plan>/<name>.mp4
```

Clip scenarios (`greybox_clip`, `toolkit_reel`, a game's own) pace the action
for watching. Check `git status` afterwards: `override.cfg` must be gone.

## 7. Evidence

`docs/qa/<plan>/README.md`:

```md
# Plan <NNN>: evidence

Measured <date> in the exported macOS app and in Chrome.

| Check | Result |
|---|---|
| GUT and the content lint (`tools/test.sh`) | PASS: N tests |
| <scenario> in the macOS app | PASS |
| <scenario> in Chrome (`browser-qa.ts`) | PASS, warm pass |
| Room tour (`--qa=rooms --part=<id>`) | PASS. Video memory a-b MiB, loads a-b ms, frame p95 a-b ms |
| The web pack | N MB |
```

Then append a UTC-stamped entry to `docs/agent-board.md` and update the plan's
row in `plans/README.md` when the plan is done.

## 8. Deploy

```sh
tools/build/export.sh web
export VERCEL_SCOPE=<team> VERCEL_PROJECT=<project>
tools/build/deploy.sh                  # a preview deployment
tools/build/deploy.sh --prod           # production, under the operator's authorization
QA_BASE_URL=https://<project>.vercel.app bun tools/build/browser-qa.ts <scenario>
```

`deploy.sh`:
1. refuses to run without `build/web/index.pck`;
2. writes `build/web/.vercelignore` (`.env*`, `.gitignore`, `.vercel`);
3. links `build/web` to the Vercel project once
   (`bunx vercel@<pinned> link --cwd build/web --scope <team> --project <project> --yes`);
4. deploys `build/web` with the pinned CLI.

If the Vercel project is connected to git, every push to the connected branch
replaces production with an empty build. After a push: export, `deploy.sh
--prod`, then the `browser-qa.ts` check against the live URL. The lasting fix
is to disconnect git in the project's settings, which is the operator's call.

## 9. The loading shell (once per game)

`web/shell.html` is the Web preset's custom HTML shell
(`html/custom_html_shell="res://web/shell.html"`). It replaces Godot's logo
and bar with the game's own loading screen, runs `engine.init`,
`engine.preloadFile` and `engine.start` itself, and puts a click between the
download and the start so sound is allowed from the first line. A `?qa=` URL
skips the click. Its pictures live in `web/loading/` and `export.sh web` copies
them beside `index.html`; keep them small (WebP, a few hundred KB). Set the
boot splash to a plain colour with no image so the desktop build matches.
