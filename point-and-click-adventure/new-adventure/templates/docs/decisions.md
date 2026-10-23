# {{GAME_NAME}}: Decision log

Newest entries go at the bottom. **Confirmed** means the operator said it.
**Proposed** means an agent recommends it, and it stands until the operator
changes it or a plan gate replaces it. **Inherited from the kit** means the
point-and-click-adventure kit made the choice when Past was built; it stands until a new entry
here replaces it. Add to the log; never rewrite a past entry. To reverse a
decision, add a new entry that points back to the old one.

| # | Date | Decision | Status | Source / notes |
|---|---|---|---|---|
| 1 | {{DATE}} | **Engine:** Godot 4.7.2, GDScript only. No C#, and no GDExtension unless a plan approves it. | Inherited from the kit | The browser build cannot load C# or most GDExtensions (Past #3, #19) |
| 2 | {{DATE}} | **Our own small adventure core with Dialogue Manager 4** for dialogue, not Popochiu. | Inherited from the kit | Popochiu 2.2.0 had no verb coin, uneven cutscene skipping, no per-line voice, loaded every audio cue at startup, and had camera bugs (Past #19) |
| 3 | {{DATE}} | **The Compatibility renderer** on every platform. | Inherited from the kit | The web export requires it, and both builds then look the same (Past #15) |
| 4 | {{DATE}} | **Base resolution 1920×1080** with a 16:9 letterbox. | Inherited from the kit | Past #14 |
| 5 | {{DATE}} | **Mouse only.** Esc is an optional extra. | Inherited from the kit | Past #7 |
| 6 | {{DATE}} | **Interaction:** a click runs the default verb, a 300 ms hold opens a verb coin (Look / Use / Talk), a right-click opens the inventory band. The band stays open after picking, so items combine; a click outside uses the held item; a right-click drops it. Until the coin is first used, labels add "Hold for more". | Inherited from the kit | Past #13, #36, #55 |
| 7 | {{DATE}} | **Every spoken line lives in a Dialogue Manager file with a static `[ID:…]`,** unique across the game. The ID names its voice file and is its translation key. | Inherited from the kit | Past #21 |
| 8 | {{DATE}} | **Saves:** JSON slots 1–6 and an autosave in slot 0, each with a 320×180 thumbnail. A save is `GameState` plus where the hero stands. The autosave runs only once a game is running. Older saves migrate one version at a time; newer or broken ones are refused. | Inherited from the kit | Past #34 |
| 9 | {{DATE}} | **Settings** apply the moment they change. Render at 1080p is the `viewport` stretch mode. An exported desktop game starts fullscreen; a window given on the command line is kept. | Inherited from the kit | Past #35 |
| 10 | {{DATE}} | **Hints and skipping:** clicking the hero gives a line about the first unfinished goal, more direct each ask. Cutscenes skip with a Skip button held 0.6 s, or Esc; a plain click never skips. | Inherited from the kit | Past #37 |
| 11 | {{DATE}} | **Cutscenes:** skipping fast-forwards every step to the end a watched run reaches; memories record when they end, watched or skipped; every cutscene plays in letterbox; playable memories shut exits and the menu; rewatching restores the whole `GameState`; a hotspot behind the hero takes the click. | Inherited from the kit | Past #39 |
| 12 | {{DATE}} | **Voiced lines hold for their audio, and never for stalled audio** (0.5 s still over at least 6 frames). | Inherited from the kit | Past #40 |
| 13 | {{DATE}} | **Voice ships as QOA:** 24 kHz mono WAV sources that Godot imports as QOA. | Inherited from the kit | No Vorbis encoder needed; cheap to decode in the browser (Past #41) |
| 14 | {{DATE}} | **The web build turns off Godot's shader cache.** | Inherited from the kit | With it on, saves didn't reach IndexedDB until the game quit (Past #38) |
| 15 | {{DATE}} | **Images:** Claude generates every image with `tools/images` from a request file. GPT-6.1 Sol through Codex is the default (`codex/gpt-6.1-sol`, 1672×941, no masks, $0 on the ChatGPT plan). The Vercel AI Gateway covers masks, exact sizes and anything Sol fails twice: Flare for new images, Sunburst for edits. Raws are immutable and every image keeps a receipt. | Inherited from the kit | Past #25, #28, #44, #47 |
| 16 | {{DATE}} | **Two-state rooms are edits of one composition,** so a transition restores the room in place. Alignment p90 ≤ 3 px. | Inherited from the kit | Past #18. Delete if the game has no second state. |
| 17 | {{DATE}} | **Close-ups push in, pinned to what was clicked;** with Reduce camera motion they crossfade. Writing readable in a close-up counts as read once it shows. | Inherited from the kit | Past #33, #54 |
| 18 | {{DATE}} | **NPCs are skinned paintings:** one painting each, meshed inside its alpha and skinned to 5–8 bones; motions are data. | Inherited from the kit | About 15 min per NPC and under 1 MiB of video memory (Past #49) |
| 19 | {{DATE}} | **The hero is painted by Sol over a rig's poses:** walks 8 frames per direction, other actions 2–3 key drawings on the rig's timing. | Inherited from the kit | Past #53. Sol alone could not keep a walk cycle's legs right. |
| 20 | {{DATE}} | **The game opens on a start screen** (Continue, New Game, Load, Settings, Quit; no Quit in the browser). The browser build has its own loading screen with a click that unlocks sound. | Inherited from the kit | Past #51, #52 |
| 21 | {{DATE}} | **Claude decides on its recommendations without asking:** art picks, style keys, model sheets and similar creative or technical choices. The operator reviews the results and can overrule at any time. Budgets, money beyond them, and actions outside the repository still need the operator. | {{Confirmed or Proposed}} | Past #29 |
| 22 | {{DATE}} | The game is called **{{GAME_NAME}}**. {{ONE_LINE_PREMISE}} | Confirmed | Operator brief |
| 23 | {{DATE}} | **Platforms:** {{desktop downloads, and the browser as a demo or the full game}}. | {{Confirmed}} | Operator |
| 24 | {{DATE}} | The repository is **{{REPOSITORY_URL}}** ({{public or private}}). | Confirmed | Operator |
| 25 | {{DATE}} | **Look:** {{the art style, with reference images in docs/reference/}}. | Confirmed | Operator |
| 26 | {{DATE}} | **Tone:** {{tone and closest reference}}. | Confirmed | Operator |
