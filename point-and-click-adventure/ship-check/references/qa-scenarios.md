# QA scenarios

The `Qa` autoload (`src/core/qa.gd`) runs these. On desktop:
`-- --qa=<scenario> --qa-out=<dir>`. In the browser: `?qa=<scenario>` in the
URL, which `browser-qa.ts` adds. Every scenario prints `[qa] PASS|FAIL` lines
and one `[qa] RESULT`, and exits 0 on success.

Scenarios start straight in the first room, without the start screen or the
opening, unless the table says otherwise.

| Scenario | What it checks | Notes |
|---|---|---|
| `greybox` | The sample puzzle chain end to end: look, the verb coin, taking, talking with a choice, combining in the inventory, a playable memory, using an item on a hotspot, exits | Runs the same `Playthrough` script as its GUT test |
| `greybox_clip` | The greybox chain paced for the movie writer | For reels |
| `rooms` | Tours rooms: load time, frame p95, video memory with both eras and the characters, a shot per era, every hotspot answers Look | `--rooms=a,b` or `--part=<id>` (presets the part's story flags). Fails past 400 MiB, 1 s or 16.7 ms p95 |
| `npc` | Each NPC's motions (idle sway, talk bends, one-shots), with a shot of each | |
| `hero_anims` | Every hero animation in every direction plays past its middle; one-shots end and return to idle | |
| `saves` | Saves, changes room, loads back | In the browser, the second pass (`qa-pass=2`) checks the save survived the reload |
| `reduced_motion` | The opening and a close-up with Reduce camera motion on: crossfades, no zoom | Starts from the opening |
| `menus` | Shoots the top bar, the hotspot reveal and each menu page | |
| `skip` | Holds the Skip button during the opening and checks it fast-forwards to the first room | Starts from the opening |
| `title` | The start screen: Continue, New Game, Load, Settings, Quit (no Quit on the web) | The only scenario that shows the start screen |
| `perf` | Frame times through a set route, plus memory. Prints one `[qa] PERF {json}` line | `--uncapped` turns vsync off. Starts from the opening |
| `vista` | A discovery reveal and its memory vista | |
| `journal` | Reads a clue, sees a memory, opens the journal and checks the entries | |
| `reveals` | Shoots each discovery reveal | Long timeout |
| `voice` | Plays a registered 1 s tone as a line: the line holds for its audio, the envelope drives `Voice.level()` and the hero's voice level | Prints the longest frame while it played |
| `toolkit_reel` | One of each cinematic kind, paced for the movie writer | For reels |

## A game's own scenarios

Each part of the story adds a playthrough scenario named after the part
(`--qa=<part>`), running the part's `Playthrough` script, the same one its GUT
test runs. A whole-game scenario can chain them. Give long ones their own
timeout in `TIMEOUTS`, call `_mark(step)` at each step so a timeout names it,
and add the scenario to `WITH_OPENING` if it should start from the opening.

## Writing a scenario

- Drive input through `Interaction` (clicks at a hotspot's `focus_point()`,
  verb picks, inventory slots), never the real mouse; the autoload swallows
  real mouse events during a run.
- `_check(ok, what)` for each assertion, `_shot(name)` for evidence,
  `_mark(step)` before each step.
- `_settle()` waits for walks, lines and transitions to finish.
- Skip lines by connecting to `Say.line_started` and calling `Say.skip`
  deferred, unless the scenario measures them.
