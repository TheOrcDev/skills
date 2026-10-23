# {{GAME_NAME}}: Technical Plan

Status: draft, {{DATE}}. Inherited from the point-and-click-adventure kit, whose engine and
browser facts were checked against Godot 4.7.2's docs and source when Past was
built. Record every deviation here, with the plan that made it.

## 1. Versions (pinned)

| Component | Version | Notes |
|---|---|---|
| Godot | **4.7.2-stable**, `4.7.2.stable.official.ed1daf0bf` | Check the macOS zip and the export templates against the release's `SHA512-SUMS.txt`. |
| Dialogue Manager | **4.1.0**, tag commit `a719088` | Nathan Hoad's dialogue add-on, MIT. Fetched from the tag tarball by `fetch_addons.sh`, which checks its SHA-256. |
| GUT | **9.7.1**, tag commit `aeb5d4f` | Unit tests, MIT. Fetched the same way. |
| Blender | 4.5 LTS | The hero's pose rig (`art-pipeline.md` §5C) |
| Python (tools) | 3.12 via `uv` | The system Python may be too new for parts of the ML stack |
| Bun | {{VERSION}} | `tools/audio`, `tools/images`, `tools/build/serve.ts`, `browser-qa.ts` |
| AI SDK (`ai`) + Vercel AI Gateway | pinned in `tools/images/package.json` | The gateway image engine. The key is `AI_GATEWAY_API_KEY` in `.env`. |
| Codex CLI | {{VERSION}} | Sol (`codex/gpt-6.1-sol`), the default image engine |
| ffmpeg, git-lfs, jq | installed | Media processing, repository, the web export's part filter |

- Scripts find Godot through `GODOT_BIN`, which defaults to
  `$HOME/Applications/Godot-4.7.2.app/Contents/MacOS/Godot` (`tools/godot.sh`).
- Versions change only through a plan.

## 2. Platforms and builds

| Build | What | Where |
|---|---|---|
| **Desktop** | macOS universal, Windows, Linux | {{STORE: itch.io downloads, Steam later}} |
| **Browser** | {{the full game or a demo part}}, exported for the web | {{HOST: Vercel or itch.io}} |

- **Renderer:** Compatibility everywhere (OpenGL 3.3 on desktop, WebGL 2 in the
  browser), so both builds look identical. It renders in 8-bit colour, with no
  debanding and no 2D HDR. Fog gradients get grain or dithering.
- **Browser export:**
  - Single-threaded (the default since 4.3), so it needs no special server
    headers.
  - Needs WASM SIMD: Chrome 91+, Firefox 89+, Safari 16.4+. Chrome and Firefox
    are the targets. Safari is best effort.
  - The engine `.wasm` is 39.5 MB raw, about 10 MB gzipped and 6.9 MB with
    Brotli.
- **itch.io browser limits:** at most 200 MB per file, 500 MB in total and 1,000
  files.
- **Desktop template sizes** before the `.pck`: Windows 109 MB, Linux 74 MB,
  macOS universal 124 MB zipped.
- **macOS distribution:** a public build needs Developer ID signing and
  notarization. That needs an Apple Developer account, which the operator
  decides on before the first public desktop build.
- **Steam:** GodotSteam is a GDExtension, so it ships in desktop builds only.

## 3. Project layout

The repository root is the Godot project root.

```
{{game}}/
  project.godot
  addons/dialogue_manager/   # Dialogue Manager 4.1.0 (fetched, pinned)
  addons/gut/                # GUT 9.7.1
  addons/adv_tools/          # scaffolds, lint, sprite import (run by Godot)
  src/
    core/                    # adventure core (section 5)
    systems/                 # eras, flashbacks, cinematics, voice, journal, hints, hero (section 6)
    ui/                      # verb coin, inventory, subtitles, top bar, menus, start screen
    shaders/
  content/
    chapters.json            # the parts, and the rooms, close-ups, characters and dialogue in each
    rooms/<room_id>/         # <room_id>.tscn, <room_id>.gd, art/
    characters/<id>/         # actor scene, sprite sheets or painting, anchors
    closeups/<id>/
    items/<id>/              # item resource and icon
    dialogue/<part>/         # *.dialogue: every spoken line in the game
    cutscenes/<id>/
    hints/goals.gd  journal/entries.gd
  assets/                    # shared shipping assets
    audio/voice/en/  audio/music/  audio/ambience/  audio/sfx/  audio/ui/  fonts/  textures/
  test/                      # GUT tests
  web/shell.html             # the browser build's loading screen
  tools/                     # .gdignore: images, art (adv-art), audio, blender, build
  art-source/  audio-source/ # .gdignore: requests, raws, work files, masters, manifests
  docs/  plans/              # .gdignore
  build/                     # gitignored export output, with a .gdignore
```

- Scripts that Godot runs live in `addons/adv_tools/`, not in `tools/`:
  `new_room.gd`, `new_closeup.gd`, `new_item.gd`, `new_npc.gd`,
  `new_reveal.gd`, `scaffold_core.gd`, `import_sprites.gd`,
  `new_bus_layout.gd` and `lint.gd`.
- Scenes are created by scaffolds that save through Godot, so resource IDs stay
  valid. They are then edited in the editor or by script. A `.tscn` is never
  hand-assembled.
- **Git LFS** from day one covers `png webp jpg ogg wav mp3 mp4 webm ogv blend
  kra psd glb fbx zip`. `.env` and `build/` are gitignored, and Godot's
  `*.import` files are committed.

## 4. Project settings

| Setting | Value |
|---|---|
| Viewport | 1920×1080, stretch mode `canvas_items`, aspect `keep` (letterbox) |
| Renderer | `gl_compatibility` for every rendering method, including mobile and web |
| 2D texture filter | Linear. Mipmaps only where a layer is drawn well below its size (§8). |
| Window | An exported desktop game starts in borderless fullscreen, with a windowed option in Settings. The editor, tests, QA runs and the browser start in a window, and so does any run given a window size or mode on the command line. |
| Input | Mouse buttons only. Esc (`ui_cancel`) is an optional extra that skips the opening and closes pages and close-ups. |
| Audio buses | Master → Voice, Music, Ambience, SFX, UI. No bus effects (§7). Written by `new_bus_layout.gd`. |
| Localization | {{SOURCE_LANGUAGE}} source. Dialogue Manager exports POT templates when translation starts. |
| Navigation | `navigation/world/map_use_async_iterations` and `region_use_async_iterations` are off. With them on, a fresh room's walk area becomes usable only about 10 physics frames after it loads. |
| VRAM compression | `import_etc2_astc` is on, because the universal macOS export refuses to build without it. 2D art still imports lossy or lossless (§8). |
| Web shader cache | `rendering/shader_compiler/shader_cache/enabled.web=false` (§7) |
| Dev window | 1600×900 window override for development runs |
| Boot splash | No image, a plain background colour |

## 5. Adventure core (`src/core`)

The core is small, code-first and tested. Godot does the heavy lifting:
navigation, y-sorting, `Parallax2D`, `AnimationPlayer`, `Camera2D`.

### 5.1 Rooms

Each room is one scene in `content/rooms/<room_id>/`. Its script extends
`Room`.

```
Room
  Layers/        Now/, Then/     # Parallax2D and Sprite2D layers, grouped by era
  WalkAreas/     Now, Then       # NavigationRegion2D per era; one is active
  ScaleZones/                    # far and near lines (y, scale); linear in between
  Hotspots/                      # Hotspot = Area2D + CollisionPolygon2D, tagged with an era
  Exits/                         # Exit hotspots: target room and entry marker
  Markers/                       # entry points and cinematic marks (Marker2D)
  Actors/                        # y-sorted: the hero, NPCs, occluders with baselines
  Foreground/                    # framing layers above the actors
  Cinematics/                    # this room's AnimationPlayer and CinematicCamera
```

**Hooks:**

| Hook | When |
|---|---|
| `_on_enter(from)` | Loaded but not yet shown |
| `_on_shown()` | Visible |
| `_on_exit()` | Leaving the room |
| `_on_restore()` | After a save is loaded |

A room's state is a dictionary kept in `GameState`. A room's script answers
verbs as `look_<hotspot>()`, `use_<hotspot>()`, `talk_<hotspot>()` and
`item_<hotspot>(item)`.

**The `Rooms` autoload:** `await Rooms.goto(&"<room_id>", &"<marker>", &"fade")`.

1. Loads the room. On desktop on a background thread; in the single-threaded
   browser build synchronously, so rooms stay light.
2. Places the hero at the entry marker.
3. Plays the transition.
4. Frees the old room.
5. Autosaves.

### 5.2 Actors

- **`Actor`** (Node2D): `await walk_to(point)` follows a path from
  `NavigationServer2D` on the active walk area.
- **Facing** comes from velocity or from `face(dir)`.
- **Depth scale** comes from the room's ScaleZones.
- **Speech:** `await say(&"LINE_ID")` hands the line to Dialogue Manager (§5.6).
- **Movement can be cancelled** by a new click.
- **Speed:**
  - A body with a recorded ground speed sets the walk speed.
  - `depth_speed` slows vertical motion, which is movement in depth (0.6×).
  - With `step_with_frames`, the actor moves one frame's worth of ground each
    time a new frame shows, so the planted foot never slides.
- **Bodies:** `SpriteBody` plays frame animations (the hero), and `RigBody`
  plays a skinned painting's data motions (NPCs).
- **The hero** is an `Actor` whose presentation is `HeroBody` (§6.4).

### 5.3 Animation naming

- Names are `<anim>_<dir>`, with `dir` one of `r`, `l`, `u`, `d`, plus `ur`,
  `ul`, `dr` and `dl` if diagonals are made.
- A missing `_l` mirrors `_r`, and other missing directions fall back to the
  nearest one made.
- Loops (`idle`, `walk`, `talk`) are never awaited.
- One-shots (`pickup_low_r` and so on) end in `animation_finished`, and the
  `Actor` returns to idle. A walk or another one-shot interrupts a one-shot,
  and `await actor.play(...)` returns either way.
- While an actor speaks standing still, it plays its `talk_animations` in turn,
  one per line (`talk_a`, `talk_b`).
- An `IdleFidgets` child plays a random fidget after 9–18 s of uninterrupted
  idling, unless input is locked (`fidget_a`, `fidget_b`, `look_around`).
- The hero's set: `idle`, `walk`, `talk_a`, `talk_b`, `pickup_low`,
  `pickup_high`, `use`, `give`, `look_around`, `fidget_a`, `fidget_b`,
  {{EXTRA_ANIMATIONS}}.

### 5.4 Interaction

The `Interaction` autoload handles all input (`game-design.md` §8).

- **Hover:** a physics point query finds the topmost `Hotspot` under the
  cursor, which sets the label and the cursor shape. `pick_priority` breaks
  ties (`Area2D` already has a native `priority`).
- **Clicks:**
  - a short click runs the hotspot's default verb;
  - a press held for 300 ms or more opens the verb coin;
  - a double-click on an exit leaves at once;
  - a right-click opens the inventory or drops the held item.
- **Dispatch:**
  1. The hero walks to the hotspot's `walk_to` marker and faces it.
  2. Then the hotspot's verb runs: `on_look()`, `on_use()`, `on_talk()`,
     `on_item(item)`, or the room's `<verb>_<hotspot>()`.
  3. Anything unhandled plays a random fallback line for that verb.
- Input is locked while a cutscene or dialogue choice is running. Clicks are
  ignored, not queued.
- A hotspot behind the hero takes the click. Clicking the hero asks for a hint
  only where nothing usable is behind.
- Until the player first picks a verb on the coin (`coin_learned` in
  `settings.cfg`), a hotspot's label adds "Hold for more" where the coin offers
  a verb the click doesn't.
- Synthetic input events drive the integration tests (§9).

### 5.5 Inventory

- **Items:** an `ItemDef` resource holds an id, a name key, an icon, a look-line
  id and its combinations. `new_item.gd` makes them from a JSON list, at
  `content/items/<id>/<id>.tres`.
- **The `Inventory` autoload:** `add`, `remove`, `has`, the `held` item, and
  signals for the UI. Its contents live in `GameState`.
- **The band** (`InventoryPanel`): a left-click picks an item onto the cursor
  and the band stays open. A left-click on another item then combines the two,
  and on the held item puts it back. A left click outside the band closes it
  and uses the held item on whatever is under the cursor. A right-click closes
  it and drops the item.

### 5.6 Dialogue: Dialogue Manager 4

- **Every spoken line** lives in a `.dialogue` file: conversations, look
  lines, barks, hints, journal lines and fallbacks.
- **Every line carries a static `[ID:SOME_KEY]`,** unique across the game. The
  ID names the line's voice file and is its translation key. Cues (`~ cue`) are
  unique within a file.
- **Voice direction** is a tag on the line, never spoken text:
  `[#vo=whispers]`.
- **Choice trees** use Dialogue Manager's responses and conditions. Options are
  exhausted through `GameState` flags. Mutations call into `GameState`,
  `Inventory` and the era system.
- **Our own balloon** shows the line above the speaker in that speaker's
  colour, then passes the line's ID to `Voice` (§6.5).
- Scripts speak through one wrapper: `await Say.line(&"<file>", &"<cue>")`.
- Dialogue Manager 4.1.0 syntax: `~ cue`, `[ID:…]`, `[#tag]`, and
  `DialogueLine.static_id` carries the ID.

### 5.7 Game state and saves

- **`GameState`** keeps one versioned dictionary:
  - flags and inventory;
  - room states and the current room and entry;
  - eras and memories seen;
  - journal facts and cutscenes seen;
  - hint progress;
  - dialogue variables (flags hold a bool, a number or text).
- **Saves** (the `Saves` autoload):
  - JSON at `user://saves/slot_<n>.json`, with a 320×180 thumbnail beside it as
    `slot_<n>.png`. Slots 1–6 are manual, and slot 0 is the autosave.
  - A save is `GameState.to_dict()` plus where the hero is: the room, the
    entry, the position and the room's era. Loading applies the state, then
    goes to the room and places the hero while the screen is still black.
  - The autosave is written each time a room is shown, but only once
    `main.gd` has started a game, so tests and tools never write one. QA runs
    keep their saves in `user://qa-saves`.
  - Migrations run one step at a time, as `_migrate_from_<n>`, up to
    `GameState.SAVE_VERSION`. A save from a newer build, or one that isn't a
    save, is refused and the game is left alone.
  - In the browser, `user://` is IndexedDB, and saves survive a page reload.
    The engine copies a write into IndexedDB a second or two later. The
    `saves` QA scenario checks this over two `browser-qa.ts` passes.
- **Settings** are stored separately (§6.9).

## 6. Custom systems

Each is a small autoload or scene with one job, on top of the core.

### 6.1 Eras and flashbacks: `Flashback` (autoload)

{{Delete or trim if the game has no second state.}}

- **Eras:** `now` and `then`. A room with a past carries both eras' layers,
  hotspots and walk areas in one scene. `Rooms.current.set_era(&"then")` shows
  or hides the tagged nodes and activates that era's walk area. The room stays
  at the same coordinates, so the hero stays put and the two images line up.
- **Vision** (cinematic): `await Flashback.vision(id, room, anchor, during)`.
  Locked input, letterbox, skippable. Finishing, watched or skipped, records
  the memory in `GameState`.
- **Playable memory:** `Flashback.enter_memory(id, room, anchor, done)`. The
  room stays in the other era for play, with its exits and the save menu shut,
  until `done` (a flag name or a callable) holds. A verb starts it without
  await.
- **Memory vista:** a reveal (§6.3) played in the then era.
- **Separate rooms:** a memory whose geography is too different uses a separate
  room and a crossfade. That is the exception.

### 6.2 Flashback transition shader

A full-screen effect that runs both ways: `progress` 0→1, an `origin` where the
bloom starts, a tileable `noise` for the dissolve front, a small `warp`,
`grade_mix` between the two grades, and a `flare` scaled by Reduce flashing.
The two era layer groups are composited by a noise-offset radial distance from
`origin`, with the characters drawn above. Blending two textures is cheaper in
the browser than stacking screen reads, screen-texture mipmaps are broken in
browser builds, and particles inside a `CanvasGroup` vanish in WebKit.

### 6.3 Cinematics: `CinematicCamera`, `Reveal`, `Letterbox`, `Cutscenes`

- **`CinematicCamera`:** a `Camera2D` made current for a shot, with paths in an
  `AnimationPlayer`.
- **Zoom stack** (`Reveal`): nested ring textures at scales 1, 2, 4 …, zoomed
  in log space about one fixed point, crossfading at the ring boundaries. Inner
  rings ship as one-byte grey and `ring_feather.gdshader` fades their edges.
- **Discovery reveal:** `new_reveal.gd` builds a `RevealStage` scene from a
  reveal spec: the zoom stack, the hero, an optional title and the "reveal"
  animation. `RevealCutscene` plays it as a cutscene.
- **The cutscene runner** (`src/systems/cinematics`):
  - A cutscene is a `Cutscene` script whose `run(c)` awaits steps: `c.walk`,
    `c.face`, `c.anim`, `c.say`, `c.wait`, `c.shot`, `c.fade` and `c.era`.
  - **The `Cutscenes` autoload** locks input, brings in the letterbox bars and
    arms its own Skip button.
  - **Skipping fast-forwards:** later steps finish instantly (walks teleport,
    lines stop, animations seek to their end, tweens complete) and the
    script's own logic still runs, so a skipped scene leaves the world exactly
    as a watched one does. Anything that changes the world belongs in the
    script, never in animation method keys.
  - **Skip control:** appears when the mouse moves and fires after a 0.6 s
    hold. Esc also skips.
  - **Rewatching:** every named cutscene is registered for the journal.
  - **Reduce camera motion** shortens moves or replaces them with crossfades.

### 6.4 The hero's presentation: `HeroBody`

- `CharacterSprites` holds the frames and per-frame anchors. `SpriteBody`
  plays them. `HeroBody` (`src/systems/hero/hero_body.gd`) adds the hero's
  extras.
- **Sprites:** {{HERO_ROUTE: painted over the rig's poses
  (`painted-hero` skill) or rendered}}. Walks have {{N}} frames at {{FPS}}
  fps with frame-locked stepping. Other animations are limited animation:
  a few key drawings, each held for the frames of the rig's animation whose pose
  is nearest. A held drawing breathes by under 1%.
- `import_sprites.gd` builds the `SpriteFrames` from the manifest, one
  animation per name and direction, with per-frame events (`step` on each heel
  strike, `grab` when the hand closes). `SpriteBody.animation_event` fires
  once each time such a frame shows.
- **Anchors** (eyes, head, shoulders, hands, feet) are mirrored when facing
  left. `SpriteBody.hold(texture, hand)` keeps an item at a hand anchor until
  `release()`.
- **Eyes** (optional): sprites at the eye anchors with idle, blink, narrow,
  wide and flare states, following the voice envelope.
- **Frames:** grey + alpha (LA8) or RGBA, trimmed, imported lossless, inside
  the hero's video-memory budget (§10).

### 6.5 Voice and subtitles: `Voice` (autoload)

- `Say` calls `Voice.play(id)` with the line's static ID. `Voice` loads
  `assets/audio/voice/en/<ID>.wav`, imported as QOA, when the line is said.
- The line plays on the Voice bus, and the subtitle stays up until the audio
  ends. A click skips the line and stops its audio.
- `Voice.register(id, stream, envelope)` makes a line sayable without files,
  for tests and previews.
- **Envelopes:** about 30 loudness values per second, computed offline by
  `tools/audio post` into `assets/audio/voice/en/envelopes.gd`. `Voice.level()`
  reads the value at the audio's position, and a mouthless character's eyes or
  an NPC's talk bends follow it.
- **Missing audio** falls back to text timing and shows up in the lint.
- **Stalled audio:** a line whose audio stands still for 0.5 s, over at least
  6 frames, is stopped and keeps the time it would have had as text. That
  happens in a browser before the player's first click (§7).

### 6.6 Interface

- **Top bar and pages** (the `Menus` autoload): the bar slides down when the
  cursor pushes against the top edge, only while the player is free to act.
  Pages (`MenuScreen`) sit over the paused game: Save and Load slots with
  thumbnails, Settings, the journal, and the start screen as Main menu. QA runs
  switch the bar off.
- **Reveal hotspots** marks everything usable for 2.6 s.
- **Hint on the hero** (the `Hints` autoload): the goal is the first one in
  `content/hints/goals.gd` whose flag isn't set or whose memory isn't seen.
  The lines are the cues `<goal>_1`, `<goal>_2` … in
  `content/dialogue/hints.dialogue`, each one more direct, counted in
  `GameState`. `none` plays once every goal is done.
- **Start screen:** Continue (the newest save), New Game, Load Game, Settings,
  Quit (not in the browser), over {{TITLE_BACKGROUND}}, blurred once at load.

### 6.7 Journal

`content/journal/entries.gd` lists memory titles and their lines, fact texts,
and the cutscenes that can be watched again. Stills are captured the first time
a memory shows, at 640×360, in `user://journal/`. `Journal.rewatch(id)` plays a
cutscene, then puts back the room, the hero's place and the whole of
`GameState`.

### 6.8 Saves

See §5.7.

### 6.9 Settings

One `Settings` autoload keeps them in `user://settings.cfg`, apart from saves.
Each applies as soon as it is set: the volumes, subtitles and their size, text
speed, Reduce flashing, Reduce camera motion, Fullscreen (in a browser only
from a click), and Render at 1080p (the `viewport` stretch mode; Godot has no
2D render scale for the root viewport). Tests and QA runs use their own
settings file at the defaults.

### 6.10 Pre-rendered video (later, optional)

Only if a video cutscene is approved. Desktop: `VideoStreamPlayer` with Theora
`.ogv`, at most 1080p30. Browser: an HTML `<video>` (MP4, H.264 + AAC) over the
canvas through `JavaScriptBridge`, started from a click.

### 6.11 Close-ups: `Closeup`, `Closeups`

- A close-up lives in `content/closeups/<id>/`: a `Closeup` root, a 1920×1080
  `Background` and `Hotspots`, built by `new_closeup.gd`. Its script answers
  verbs as `<verb>_<id>()`.
- **Opening:** `Closeups.open(id, hotspot)`. A screen-shaped frame is fitted
  round the hotspot, a camera zooms until it fills the screen (0.9 s, eased),
  and the close-up stays pinned over the frame and fades in with soft edges.
- **Closing:** the same move reversed, from a right-click, Esc or ‹.
- Writing large enough to read counts as read once the close-up is on screen.
- With Reduce camera motion it crossfades in, full screen, with no zoom.

## 7. Browser build specifics

- **Loading screen:** `web/shell.html` is the Web preset's custom HTML shell.
  {{LOADING_SCREEN: what it shows while the pack downloads}}. When the
  download ends, a click starts the engine, so sound is allowed from the first
  line. `?qa=` runs skip the click.
- **Audio:** the browser's default "Sample" playback cannot run bus effects,
  decodes a whole clip on the main thread the first time it plays (freezing on
  long clips), and never frees decoded audio. So:
  - voice and music players use `playback_type = Stream`;
  - short effects stay on Sample and are decoded during loading with
    `AudioServer.register_stream_as_sample()`;
  - nothing depends on bus effects: filtered variants are rendered offline, and
    ducking uses volume tweens;
  - pitch variety comes from pre-rendered variants.
- **Sound waits for the first click,** and is mixed on the main thread between
  frames, so a long frame holds sound back.
- **Loading:** the whole `.pck` downloads before the game starts. The `.wasm`
  memory cap is 2 GiB.
- **Shaders:** Compatibility cannot precompile shaders, so each is drawn once
  during loading.
- **Avoid in WebKit:** `clip_children` and particles inside a `CanvasGroup`.
- **Saves:** `user://` lives in IndexedDB, so clearing site data deletes them.
- **No shader cache** on the web: otherwise compiled shaders keep writing into
  `user://`, and saves don't reach IndexedDB until the game quits.

## 8. Import settings

- **Backgrounds and layers:** lossy (WebP) or lossless, no VRAM compression for
  2D, mipmaps only for layers drawn below about 60% scale.
- **Maximum texture size:** 4096 px per side. Larger panoramas are tiled.
- **Memory reference:** a full-screen 1920×1080 RGBA8 layer uses 7.9 MiB of
  video memory, and a 4096² texture 64 MiB (85 MiB with mipmaps).
- **Character frames:** trimmed, packed one sheet per animation, imported
  lossless (painted ink blocks up under compression).
- **Voice:** 24 kHz mono WAV sources that Godot imports as QOA (about 77 kbps).
  The export carries the QOA, never the WAV.

## 9. Testing and QA

- **Unit tests:** GUT 9.7.1, in `test/`, run headless. They cover path
  following, facing and the animation fallbacks, ScaleZones, verb dispatch,
  inventory combinations, the era system, saves and migrations, cutscene
  fast-forward and voice IDs.
- **Integration tests** load a room headless, drive `Interaction` with
  synthetic input, and assert the results. Each part's `Playthrough` plays the
  whole part the way a player's mouse would.
- **Every room tested** (`test_rooms_all.gd`): its walk area and default
  marker, every hotspot answers Look, every exit lands on a marker that exists.
- **Content lint** (`addons/adv_tools/lint.gd`): every dialogue line has an
  ID, unique across the game; cues are unique per file; every hotspot answers
  Look; every room has an active walk area and entry markers; no asset is
  orphaned.
- **Tool tests:** `bun test` in `tools/images` and `tools/audio`, `pytest` in
  `tools/art`.
- **One command:** `tools/test.sh` runs the import pass, GUT and the lint, with
  logs in `build/test-logs/`.
- **Build checks:**
  - **Desktop:** `tools/build/export.sh macos`, then
    `<app binary> -- --qa=<scenario> --qa-out=<dir>`. The `Qa` autoload plays a
    scripted sequence, saves screenshots, prints PASS or FAIL lines and sets the
    exit code.
  - **Browser:** `tools/build/export.sh web`, `bun tools/build/serve.ts`, then
    `bun tools/build/browser-qa.ts <scenario>`. It opens a visible Chrome window
    with a throwaway profile and backgrounding off, passes `?qa=<scenario>`, and
    prints the `[qa]` lines, console errors and crashes. An automation tab
    reports `document.hidden`, and Godot then only advances when a screenshot
    forces a frame.
  - **Scenarios:** `greybox`, `greybox_clip`, `rooms` (`--part=<id>` or
    `--rooms=a,b`), `npc`, `hero_anims`, `saves`, `reduced_motion`, `menus`,
    `skip`, `title`, `perf`, `vista`, `journal`, `reveals`, `voice`,
    `toolkit_reel`, plus each part's playthrough.
  - **Movies:** `--write-movie` takes the window size from the project
    override, so put a temporary `override.cfg` with a 1920×1080 window
    override in the root while recording.

  Evidence goes in `docs/qa/<plan>/`. A scenario that times out names the step
  it was on.

## 10. Budgets

| Metric | Desktop | Browser |
|---|---|---|
| Frame rate at 1080p | 60 fps on {{REFERENCE_MACHINE}} and a 2020-era integrated GPU | 60 fps in Chrome |
| Video memory per room | 400 MiB or less, both eras plus characters (Past measured 182–224 MiB) | Same |
| The hero's loaded frames | 128 MiB or less | Same |
| Room load | 1 s or less | 2 s or less (no threads) |
| Download | Aim for 4 GB or less | `.pck` of {{WEB_PACK_BUDGET}} MB or less, plus about 10 MB of engine (gzip) |
| Peak memory | no cap | 1 GiB or less of the 2 GiB cap |
| Voice | QOA mono at 24 kHz, about 77 kbps | Same |

## 11. Risks

| Risk | Mitigation |
|---|---|
| Our own adventure core costs time and can have bugs | Keep it small, lean on Godot's built-ins, test it with GUT |
| Dialogue Manager is one maintainer's add-on | Pinned (MIT). Its files are plain text, so in the worst case we parse the subset we use. |
| Stream audio latency in the single-threaded browser build | Measure in the voice spike. A threaded build is the last resort. |
| 8-bit banding in gradients | Grain and dithering |
| Safari / WebKit quirks | Best effort. Avoid the known bad patterns (§7). |
| macOS notarization needs a paid Apple Developer account | Operator decision before the first public desktop build |
| Repository size | LFS from day one. Check the LFS quota before the first push, and keep bulky intermediates out of git. |
