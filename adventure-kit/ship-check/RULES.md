# ship-check rules

Each rule has its reason and the Past evidence that set it.

## What counts as done

1. **Done means the desktop export and the web export, not the editor.** The
   editor hides import, export-filter and browser problems. Past's browser
   saves, audio and pack size all broke in ways the editor never showed.
2. **QA runs in the exported app.** `build/macos/<Game>.app/Contents/MacOS/<Game>
   -- --qa=<scenario> --qa-out=<dir>`. Without `--qa` the `Qa` autoload does
   nothing, so shipping it costs nothing.
3. **Scripted runs are isolated from the player.** A QA run keeps its saves,
   journal and settings in `user://qa-*`, starts from default settings, skips
   the start screen (except the `title` scenario), and ignores the real mouse,
   so a stray click cannot send the hero off script.
4. **A scenario that times out names its step.** Scenarios call `_mark(step)`;
   the result reads `timed out at <step>`. Long scenarios have their own
   timeouts (rooms 900 s, a part's playthrough 600 to 900 s, the whole game
   3,600 s).
5. **Evidence goes in `docs/qa/<plan>/`.** Screenshots, the `[qa]` lines, the
   measurements, reels and a README with a checks table. A reviewer reads the
   README, not the terminal.

## Tests and lint

6. **`tools/test.sh` is the one command.** Import pass, GUT, lint; logs in
   `build/test-logs/`; non-zero exit on any failure. The import log is grepped
   for `SCRIPT ERROR` and `^ERROR`.
7. **Tests never touch the player's settings or saves.** A GUT pre-run hook
   points settings at `user://test-settings.cfg` and resets them.
8. **The lint guards content.** Every line has an ID and direction where
   needed, IDs are unique game-wide, cues are unique per file, every hotspot
   answers Look, every room has a walk area and entry markers, and no asset is
   orphaned. Past's lint learned the duplicate-ID rule after two chapters
   reused cue names and broke the hints.
9. **Known noise is not a failure.** Headless runs and the desktop app may
   print "resources still in use at exit" or "ObjectDB instances leaked" when
   they quit. With `--verbose` the leftovers are the dialogue addon's script and
   the last dialogue file it ran.

## The web build

10. **Compatibility renderer everywhere.** WebGL 2 in the browser, OpenGL 3.3
    on desktop, so both builds look the same. 8-bit colour: fog banding is
    hidden with grain and dithering.
11. **Single-threaded web export.** No special server headers needed. Rooms
    load synchronously there, so a room must load in 2 s or less, against 1 s
    on desktop.
12. **The shader cache is off on the web**
    (`rendering/shader_compiler/shader_cache/enabled.web=false`). With it on,
    Godot wrote compiled shaders into `user://` and those writes kept saves
    from reaching IndexedDB until the game quit. A browser never quits: Past
    lost saves on reload in 4 of 5 runs. With it off, 3 of 3 passed.
13. **The loading shell ends with a click.** `web/shell.html` runs the
    engine's `init`, `preloadFile` and `start` itself, with a click between
    the download and the start, so the browser allows sound from the first
    line. `?qa=` runs skip the click.
14. **Sound waits for a click; a line never waits for sound.** Before the
    first click a voice line's audio never starts. The `Voice` autoload finds
    it stalled after 0.5 s and the line keeps text time. Past's first browser
    voice run timed out waiting for audio that would never play.
15. **Voice and music stream in the browser.** Sample playback freezes on the
    first play of a long clip and never frees decoded audio.
16. **Avoid in WebKit:** `clip_children`, and particles inside a `CanvasGroup`.
17. **Each shader is drawn once during loading.** Compatibility cannot
    precompile, so a first transition would stutter otherwise.
18. **The whole pack downloads before the game starts.** There is no
    streaming. Keep the pack small and the loading screen in the game's style.

## Browser QA

19. **An automation tab reports `document.hidden`.** A hidden tab throttles
    `requestAnimationFrame`, so Godot only advances when a screenshot forces a
    frame. For a manual check through browser automation, take a burst of
    small screenshots to let a walk or a line play out.
20. **For timings, use `browser-qa.ts`.** It starts Chrome in a visible window
    with a throwaway profile and backgrounding off
    (`--disable-backgrounding-occluded-windows`,
    `--disable-renderer-backgrounding`,
    `--disable-background-timer-throttling`), because macOS counts a covered
    window as hidden and Chrome then stops the game's frames.
21. **Sound is allowed from the start in browser QA**
    (`--autoplay-policy=no-user-gesture-required`), as after the player's
    click.
22. **Quote the warm pass.** `browser-qa.ts` runs two passes by default, adding
    `qa-pass=<n>` to the URL; the second runs with warm caches. The `saves`
    scenario uses the second pass to check that a save outlived the reload.

## The pack

23. **Check the real file list, not the export filter.** Past's web pack grew
    to 304 MB because an image tool's scratch copies and `build/screenshots`
    sat inside the project and got imported. `export.sh` now lists the pack
    with `pck_list.py` and fails if an excluded part is still there.
24. **Godot must never import `build/`, `art-source/`, `audio-source/` or
    `tools/`.** Each carries a `.gdignore`; `tools/godot.sh` recreates
    `build/.gdignore` on every run. Scratch files go to the system temp folder.
25. **The web pack has a budget.** Past's demo targeted 150 MB (itch.io caps a
    file at 200 MB). Its hero sprites alone went from 97 MB to 6.1 MB when they
    were repacked as trimmed grey + alpha; the pack fell from 143.3 to
    52.6 MB. Run `pck_list.py --sizes` whenever the pack grows.
26. **Parts can be left out of the web build.** A part without `"web": true` in
    `content/chapters.json` is added to the Web preset's exclude filter for
    that export only.

## Budgets

27. **Every room is measured with everything loaded:** both eras, the hero and
    the room's NPCs. The `rooms` tour fails a room past 400 MiB of video
    memory, 1 s of load, or a 16.7 ms frame p95. Past's 52 rooms measured
    102 to 144 MiB after the hero was repainted (182 to 224 MiB before).
28. **The Compatibility renderer reports no GPU time.** The budget is the
    frame time itself.
29. **Fix content, not thresholds.** A room over budget gets smaller layers,
    fewer full-screen textures or trimmed sprites. A threshold changes only
    with a recorded decision.

## Reels

30. **Movies need a 1920×1080 window override.** Godot's movie writer takes
    the window size from the project override, so put a temporary
    `override.cfg` with the window size overrides at 1920×1080 in the project
    root while recording, and delete it afterwards.
31. **Force drawing while recording.** `--force-draw` keeps drawing when other
    windows cover the game; macOS otherwise stops drawing it and the movie
    gets stale frames.

## Deploy (Vercel)

32. **Pin the CLI through `bunx`** (`bunx vercel@<version>`). An old global CLI
    failed mid-upload in Past.
33. **Never upload `.env.local`.** Linking writes an OIDC token there.
    `deploy.sh` writes a `.vercelignore` into `build/web` before every deploy,
    because the export wipes the folder.
34. **A git-connected Vercel project breaks production on push.** The repo has
    no built game in it (`build/web` is gitignored), so a push to the
    connected branch deploys an empty site that 404s, and it becomes
    production. Either disconnect git in the Vercel project settings (the
    operator's call), or after every push run `tools/build/export.sh web` and
    `tools/build/deploy.sh --prod`, then check the live URL with
    `QA_BASE_URL=<url> bun tools/build/browser-qa.ts <scenario>`.
35. **Every play downloads the pack.** A public web build spends the team's
    bandwidth on each visit. Say so when the pack grows.
36. **Production deploys are outward-facing.** Deploy to production only under
    the operator's authorization for the plan being executed.
