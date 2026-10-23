# new-adventure workflow

Run every command from the game's repository root, so Bun loads `.env` and
the scripts find the project. `S` is the path to this skill.

## 1. Toolchain

| Tool | Check | Notes |
|---|---|---|
| Godot 4.7.2-stable, macOS universal | `tools/godot.sh --version` prints `4.7.2.stable` | Install at `~/Applications/Godot-4.7.2.app`, or set `GODOT_BIN`. Check the zip against the release's `SHA512-SUMS.txt`. |
| Godot 4.7.2 export templates | `ls "$HOME/Library/Application Support/Godot/export_templates/4.7.2.stable"` | Same release, same checksum check |
| Bun | `bun --version` | `tools/images`, `tools/audio`, `serve.ts`, `browser-qa.ts` |
| uv with Python 3.12 | `uv --version` | `tools/art` (`adv-art`). The system Python may be too new for the depth model. |
| Codex CLI on the operator's ChatGPT plan | `codex --version` | Sol, the default image engine |
| ffmpeg, jq, git-lfs | `ffmpeg -version`, `jq --version`, `git lfs version` | Voice post, reels, the web export's part filter, the repository |
| Chrome | | `browser-qa.ts` |
| Blender 4.5 LTS | `/Applications/Blender.app/Contents/MacOS/Blender --version` | Only for the hero's pose rig |

A wrong checksum or a missing Godot 4.7.2 build is a STOP. Never move to
another Godot version without a plan.

## 2. Create the game

```sh
$S/scripts/new_game.sh ~/projects/mygame "My Game"
cd ~/projects/mygame
$S/scripts/fetch_addons.sh .        # addons/dialogue_manager (4.1.0) and addons/gut (9.7.1)
git init -b main
git lfs install --local             # before the first commit, so images go into LFS
(cd tools/images && bun install)    # the image tool's packages
(cd tools/audio && bun install)     # the voice tool's packages
uv sync --project tools/art         # adv-art on Python 3.12
tools/godot.sh --headless --import  # must finish with no SCRIPT ERROR or ERROR lines
```

`new_game.sh` copies `template/` (the Godot project and tools) and
`templates/` (`AGENTS.md`, `CLAUDE.md`, `docs/`, `plans/`), writes the game's
name into `project.godot`, the macOS export, the web loading screen and the
docs, restores the Git LFS rules (`.gitattributes`), and copies the files the
game owns from the sibling skills: the hero's pose rig into `tools/blender/`
(painted-hero) and the prompt preambles into `art-source/style/prompts/`
(look-gate).

The operator then writes `.env` by hand:

| Variable | Used by |
|---|---|
| `GODOT_BIN` (optional) | `tools/godot.sh` and everything that calls Godot |
| `AI_GATEWAY_API_KEY` | `tools/images`, the gateway engine |
| `ELEVENLABS_API_KEY` | `tools/audio` |

Agents never write, print or commit `.env`.

## 3. Prove the template

```sh
tools/test.sh                                  # import, GUT, lint; logs in build/test-logs/
tools/build/export.sh macos
"build/macos/My Game.app/Contents/MacOS/My Game" -- --qa=greybox --qa-out="$PWD/docs/qa/001"
tools/build/export.sh web
bun tools/build/serve.ts &                     # serves build/web, prints the URL
bun tools/build/browser-qa.ts greybox          # visible Chrome, throwaway profile
```

Each QA run prints `[qa]` lines, `RESULT PASS` or `RESULT FAIL`, and sets the
exit code. A run that times out names the step it was on. Commit with
explicit paths once all three pass.

## 4. Daily commands

| Job | Command |
|---|---|
| Everything at once | `tools/test.sh` |
| Run Godot on the project | `tools/godot.sh <args>` |
| Import after art changes | `tools/godot.sh --headless --import` |
| GUT only | `tools/godot.sh --headless --script res://addons/gut/gut_cmdln.gd -gdir=res://test -ginclude_subdirs -gpre_run_script=res://test/hooks/pre_run.gd -gexit` |
| Content lint only | `tools/godot.sh --headless --script res://addons/adv_tools/lint.gd` |
| Open the editor | `tools/godot.sh -e` |

## 5. Scaffolds

Every scene comes from one of these. Each saves through Godot, so resource
IDs stay valid. Import new art first.

| Scaffold | Command | Builds |
|---|---|---|
| Room | `tools/godot.sh --headless --script res://addons/adv_tools/new_room.gd -- <room_id> [spec.json] [--replace]` | `content/rooms/<room_id>/`: scene and script from a `room_spec.json` (made by `tools/adv-art room`). The script is never overwritten. |
| Close-up | `tools/godot.sh --headless --script res://addons/adv_tools/new_closeup.gd -- <id> <spec.json> [--replace]` | `content/closeups/<id>/` from `closeup_spec.json` (`tools/adv-art closeup`) |
| Items | `tools/godot.sh --headless --script res://addons/adv_tools/new_item.gd -- <items.json>` | `content/items/<id>/<id>.tres` per entry: id, name, icon, optional `look_file`, `look_cue` and `combinations` |
| NPC | `tools/godot.sh --headless --script res://addons/adv_tools/new_npc.gd -- <npc_spec.json>` | An `Actor` with a skinned `RigBody`, from `tools/adv-art npc` |
| Hero sprites | `tools/godot.sh --headless --script res://addons/adv_tools/import_sprites.gd -- --manifest=<sprites.json> --out=res://content/characters/hero/hero_sprites.tres` | A `CharacterSprites` resource from `tools/adv-art pack` |
| Core scenes | `tools/godot.sh --headless --script res://addons/adv_tools/scaffold_core.gd [-- --replace=hero]` | `src/core/main.tscn` and `content/characters/hero/hero.tscn` |
| Reveal | `tools/godot.sh --headless --script res://addons/adv_tools/new_reveal.gd -- --spec=<reveal_spec.json> --out=res://content/cutscenes/<id>/<id>.tscn --title="<TITLE>" --place="<Place>" [--replace]` | A pull-back reveal cutscene |
| Audio buses | `tools/godot.sh --headless --script res://addons/adv_tools/new_bus_layout.gd` | `default_bus_layout.tres`: Master, Voice, Music, Ambience, SFX, UI |

Which skill drives each: rooms, close-ups and items are
[paint-room](../paint-room/SKILL.md), NPCs are
[skinned-npc](../skinned-npc/SKILL.md), the hero is
[painted-hero](../painted-hero/SKILL.md) (`tools/build/build_hero.sh` runs
the whole hero build), and reveals are
[memory-reveals](../memory-reveals/SKILL.md).

## 6. QA scenarios

Desktop: `<app binary> -- --qa=<scenario> --qa-out=<absolute dir>`.
Browser: `bun tools/build/browser-qa.ts <scenario> [canvas=1920x1080] [passes=2] [shots-dir]`,
which loads the page with `?qa=<scenario>`. `QA_BASE_URL=<url>` points it at a
deployed build. QA runs use their own saves, journal and settings, skip the
start screen and switch the top bar off.

| Scenario | Checks |
|---|---|
| `<part>` | Any part in `content/chapters.json` with a `content/story/<part>_playthrough.gd` plays that chain from a fresh state, as a player's mouse would. `greybox` is the sample's (`content/story/greybox_playthrough.gd`, also run by GUT) |
| `greybox_clip` | The greybox chain at reading pace, for `--write-movie` |
| `rooms` | Every room now and then, a Look at every hotspot, and each room's video memory. `--part=<id>` tours a part with its story flags set, `--rooms=a,b` names rooms |
| `npc` | Shoots an NPC's motions over a grey backdrop: `--npc=<id>` (default `warden`), or `--room=<id> --marker=<name>` to stand it in a room |
| `hero_anims` | Plays every hero animation in every direction and checks the sheets fit 128 MiB |
| `hero_reel` | The hero walking and acting, for `--write-movie` |
| `saves` | Saves, changes room and loads back. In the browser, pass 2 checks the save outlived the reload |
| `reduced_motion` | The opening and a close-up with Reduce camera motion on |
| `menus` | The top bar, Reveal hotspots and each page |
| `skip` | Holds Skip during the opening and checks it fast-forwards |
| `title` | The start screen |
| `perf` | Frame times and memory |
| `vista` | A discovery reveal and a memory vista |
| `journal` | Sees a memory, then opens the journal |
| `reveals` | Shoots each reveal |
| `voice` | A voiced line (a test tone) holds for its audio, its level follows the envelope, and the hero follows the level |
| `toolkit_reel` | One of each cinematic kind, for `--write-movie` |

Movie capture: Godot takes the window size from the project override, so put
a temporary `override.cfg` with `window/size/window_width_override=1920` and
`window_height_override=1080` in the root while recording, then delete it.

Evidence (screenshots, reels, numbers) goes in `docs/qa/<plan>/`.

## 7. Builds

| Job | Command |
|---|---|
| Export | `tools/build/export.sh macos\|web [release\|debug]` into `build/<target>/`. It fails if the export logs an error. |
| Web part filter | Parts in `content/chapters.json` without `"web": true` are left out of the web pack. The export fails if one is still inside. |
| What really shipped | `python3 tools/build/pck_list.py build/web/index.pck [--sizes]` |
| Serve locally | `bun tools/build/serve.ts [port]` |
| Deploy the web build | `VERCEL_SCOPE=<team> VERCEL_PROJECT=<project> tools/build/deploy.sh [--prod]` (Vercel CLI pinned through `bunx`) |

See [ship-check](../ship-check/SKILL.md) for budgets, reels and deploying.

## 8. Closing a slice

1. `tools/test.sh` passes.
2. The plan's QA scenarios pass in the exported desktop app and in Chrome.
3. Evidence is in `docs/qa/<plan>/`.
4. New choices are rows in `docs/decisions.md` (append only).
5. The plan's execution record and its row in `plans/README.md` are updated.
6. A board entry is appended to `docs/agent-board.md`, in UTC.
7. Stage explicit paths, then commit and push if the operator authorized it
   for this plan.

## 9. Replacing the greybox

The sample chain stays until the game's first part plays end to end. Its hero
is a stand-in drawn in code (`tools/build/build_hero.sh --placeholder`); the
[painted-hero](../painted-hero/SKILL.md) skill replaces it. Then:

1. `content/chapters.json`: the game's first part first. QA, saves and the
   title read the first part's `start`.
2. `src/core/main.gd`: `start_room`, `start_entry`, and `opening` (a cutscene
   script, or empty).
3. `src/ui/title_screen.gd`: `ART`, the painting behind the start screen.
4. `tools/build/loading_art.sh <room>` and `--bloom-at` in `web/shell.html`.
5. Delete the greybox: `content/rooms/greybox_*`, `content/items/{rag,oil,oiled_rag}`,
   `content/dialogue/greybox.dialogue` (and its `translations_pot_files`
   entry), `content/closeups/greybox_notice`, `content/characters/warden`,
   `content/cutscenes/greybox_vista`, `content/story/greybox_playthrough.gd`,
   `test/integration/test_greybox_chain.gd`, the greybox goals, hints and
   journal entries, and `art-source/work/{greybox,rooms/greybox_*,closeups/greybox_notice,characters/warden,reveal/greybox_vista}`.
6. The core tests that use greybox rooms (`test_flashback`, `test_saves`,
   `test_menus` and others) move to the game's own rooms at the same time.
   `tools/test.sh` names every one that breaks.

The rebuild commands for the greybox art are in `tools/README.md`.
