# new-adventure rules

Every rule here cost Past a rework, or would have. Each has its reason and
what happened in Past. A game made with the kit copies these into its own
`AGENTS.md` (the template already does).

## Engine and code

1. **GDScript only.** No C#. No GDExtension unless a plan approves it.
   - Why: the browser build cannot load C#, and cannot load most
     GDExtensions.
   - Past: Dialogue Manager ships C# variants. The exports exclude them
     (`*.cs`, the example balloons, `DialogueLabel.tscn`).
2. **The Compatibility renderer everywhere,** for every rendering method,
   including mobile and web.
   - Why: the web export requires it, and one renderer means the desktop
     game and the browser build look identical. It renders in 8-bit colour
     with no 2D HDR, so fog gradients need grain or dithering.
3. **A feature is done when it works in the exported desktop app and in the
   browser build served locally.** The editor does not count.
   - Past: saves were lost on reload only in the browser (4 of 5 runs) until
     the web shader cache was turned off. A voiced line waited forever only in
     Chrome, because the page had no permission to play sound yet.
4. **Check API names against the docs or source of the pinned release before
   writing code.** Never write them from memory.
   - Past: `Area2D` already has a native `priority`, so the hotspot field
     became `pick_priority`. Godot 4.7 has no 2D render scale for the root
     viewport, so "render scale" became a Render at 1080p switch. Dialogue
     Manager 4.1.0's syntax (`~ cue`, `[ID:…]`, `[#tag]`,
     `DialogueLine.static_id`) was read from its source, not assumed.
5. **Pinned versions change only through a plan:** Godot 4.7.2-stable,
   Dialogue Manager 4.1.0, GUT 9.7.1, Blender 4.5 LTS, and Python 3.12
   through uv.
   - Why: a version bump changes import results, API names and the web
     build's limits all at once.
   - Check Godot and its export templates against the release's SHA-512
     sums. A mismatch is a STOP.
6. **Create scenes through the scaffolds in `addons/adv_tools/` or the editor.
   Never hand-assemble a `.tscn`.**
   - Why: scaffolds save through Godot, so resource IDs and UIDs stay valid.
   - A room's script is never overwritten. `--replace` rebuilds only the
     scene.
7. **Shaders: clamp every `pow()` base to ≥ 0.**
   - Why: Apple GPUs return NaN for a negative base, and the screen goes
     black.
8. **Navigation async iterations stay off**
   (`navigation/world/map_use_async_iterations` and
   `region_use_async_iterations`).
   - Past: with the 4.7 defaults, a fresh room's walk area was unusable for
     about 10 physics frames, which broke the first walk.
9. **`import_etc2_astc` stays on.** The universal macOS export refuses to
   build without it. 2D art still imports lossy or lossless, never VRAM
   compressed.
10. **Anything that changes the world in a cutscene belongs in the script,
    never in animation method keys.**
    - Why: a skip jumps a shot to its end and passes over its method keys. A
      skipped scene has to leave the world exactly as a watched one does.
11. **Input is locked while a cutscene or a dialogue choice runs.** Clicks
    are ignored, not queued.
12. **A hotspot behind the hero takes the click.** A click on the hero asks
    for a hint only where nothing usable is behind the hero.
    - Past: the hero standing in front of an altar took the click meant for
      it.

## The browser build

13. **The web build turns the shader cache off**
    (`rendering/shader_compiler/shader_cache/enabled.web=false`).
    - Past: compiled shaders kept writing to `user://`, and a save didn't
      reach IndexedDB until the game quit. A browser never quits.
14. **Voice and music use `playback_type = Stream`.** Short effects stay on
    Sample and are decoded while loading. Nothing depends on bus effects:
    filtered variants are rendered offline, and ducking is a volume tween.
    - Why: Sample mode freezes the game the first time a long clip plays,
      never frees decoded audio (350 to 384 KB per second played), and has no
      bus effects.
15. **Sound waits for the player's first click.** The loading shell asks for
    that click, and a voiced line whose audio stalls for 0.5 s keeps its text
    timing.
16. **Avoid in WebKit:** `clip_children`, and particles inside a
    `CanvasGroup`.
17. **The whole `.pck` downloads before the game starts.** Keep rooms light
    (the browser loads them on the main thread), and keep the pack inside its
    budget.

## Content

18. **Every spoken line lives in a `.dialogue` file with a static `[ID:…]`.**
    The ID names its voice file and is its translation key, so IDs are unique
    across the whole game, and cues are unique within a file. Hotspots speak
    through `Say.line(&"<file>", &"<cue>")`.
    - Past: two late hint goals reused early cue names and broke the hints
      file. `lint.gd` now fails on both kinds of duplicate.
19. **Every hotspot answers Look, every room has an active walk area and
    entry markers, and every exit lands on a marker that exists.** The lint
    and the every-room test check these.
20. **No deaths, no dead ends, no pixel hunts.** Hotspots have hover labels
    and can be revealed.

## Repository and assets

21. **`.gdignore` in `tools/`, `art-source/`, `audio-source/`, `docs/`,
    `plans/` and `build/`.**
    - Past: scratch copies and `build/screenshots` inside the project were
      imported and shipped, and the browser pack grew from 143 to 304 MB.
22. **Scratch goes outside the project,** in the system temp folder or the
    agent's scratchpad.
23. **Git LFS from day one,** set up before the first commit:
    `png webp jpg ogg wav mp3 mp4 webm ogv blend kra psd glb fbx zip`.
    - Why: a generated raw is about 3.5 MB, and 50 rooms came to about
      1.7 GB.
    - `.godot/`, `build/`, `.env`, `node_modules/`, `.venv/` and
      `__pycache__/` are ignored. Godot's `*.import` files are committed.
24. **Files in `art-source/raw/` are never edited, renamed or deleted.**
    Processing writes to `art-source/work/`. Shipping assets go into the
    Godot project.

## Money and secrets

25. **Secrets live in `.env`, which is gitignored.** The operator writes it.
    Agents never write, print or commit it.
26. **Paid APIs go through their tools and caches only:** `tools/images` for
    images and `tools/audio` for voice.
    - Every plan that spends has a budget from the operator. The tool refuses
      to pass it, and the agent stops at 80% to report.
    - Never regenerate an accepted asset without a reason.
    - Sol through Codex runs on the operator's ChatGPT plan at $0 and needs
      no budget.

## Process

27. **Plans live in `plans/` and run in order.** Read a plan fully before
    starting, honour its STOP conditions, and update its row in
    `plans/README.md` when done. Status values: TODO, IN PROGRESS, DONE,
    BLOCKED (with a one-line reason), REJECTED (with a one-line rationale).
28. **The decision log is append-only.** Never rewrite a past entry. To
    reverse one, add a new entry that points back.
    - Confirmed means the operator said it. Proposed means Claude
      recommends it, and it stands until the operator changes it.
29. **The board (`docs/agent-board.md`) is read before work and appended to
    after every slice,** with UTC timestamps. The log is append-only.
30. **Git: stage explicit paths only.** Commit and push under the operator's
    authorization for the plan being executed.
31. **Claude decides routine art and technical picks on its recommendation,**
    and records the pick and why. The operator can overrule any pick.
    Budgets, money beyond them, and actions outside the repository still need
    the operator.
32. **Never invent story past what the operator signed.** A puzzle or scene
    that needs an unsigned fact is a STOP: ask.
33. **Change how a character looks one thing at a time,** or as one whole
    coherent redesign, and show the operator before committing.
    - Past: a leaner body, a new head and new tendrils in one pass got
      "everything go back". A full redesign from one approved model sheet,
      shown with a reel, shipped.
34. **Evidence goes in `docs/qa/<plan>/`:** screenshots, reels and
    measurements, named in the plan's execution record.
35. **Spikes measure before volume.** Prove the look, the hero's animation
    route and the voice pipeline on one room or a few lines, then write the
    volume plan from what they measured.

## Why our own core, not Popochiu

Past evaluated Popochiu 2.2.0 and dropped it:
- it had no verb coin;
- cutscene skipping was uneven and tied to a queue system that may be
  deprecated;
- it had no per-line voice, and it loaded every audio cue at startup;
- its camera had bugs;
- objects were created from an editor dock, not from scripts an agent can
  run.

Owning the input means the verb coin needs no workaround. The core stays
small and tested with GUT, and leans on Godot's navigation, y-sorting,
`Parallax2D`, `AnimationPlayer` and `Camera2D`.
