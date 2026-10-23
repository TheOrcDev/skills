---
name: new-adventure
description: Sets up a new mouse-only, fully voiced point-and-click adventure in Godot 4.7.2 from a working template. The template has an adventure core with rooms, walking with depth scale, hotspots, a verb coin, inventory, Dialogue Manager dialogue, saves, settings, hints, a journal and cutscenes. It also has scaffolds that build scenes from JSON, image, art and voice tools, GUT tests, content lint, scripted QA, and desktop and web exports. The docs skeleton covers design, the technical plan, the pipelines, decisions, a board and plans. A greybox sample game plays end to end. Use when starting a new point-and-click or adventure game, setting up "a game like Past", creating a Godot adventure project with a verb coin and inventory, or bootstrapping the point-and-click-adventure pipeline before art, story or voice work.
---

# new-adventure

A model asked to "make a point-and-click game" hand-writes a scene, wires
input from memory and never runs the build a player gets. This skill starts
from a project that already plays. Past grew from this core to 52 rooms on
desktop and in the browser, and kept that by checking every slice in both
exported builds.

Read [RULES.md](RULES.md) before the first change. Run
[WORKFLOW.md](WORKFLOW.md) commands as written.

## What you get

| Part | What it is |
|---|---|
| Adventure core | `Room`, `Actor`, `SpriteBody`, `RigBody`, `Hotspot`, `Exit`, `Interaction` (click, hold for the verb coin, right-click inventory), `Inventory`, `GameState`, `Saves`, `Settings`, `Rooms`, `Chapters`, `Say`, `Voice`, `Closeups`, `Hints`, `Journal`, cutscenes, menus and the start screen |
| Scaffolds | `addons/adv_tools/`: `new_room`, `new_npc`, `new_closeup`, `new_item`, `new_reveal`, `import_sprites`, `scaffold_core`, `new_bus_layout`, `lint` |
| Tools | `tools/images` (image requests), `tools/adv-art` (image processing), `tools/audio` (voice), `tools/build` (export, serve, browser QA, pack check, deploy, hero build) |
| Proof | GUT tests, content lint, the `Qa` autoload with scripted scenarios, `tools/test.sh` |
| Docs | `AGENTS.md`, `docs/` (design, technical plan, art and audio pipelines, decisions, roadmap, board), `plans/` with plan 001 |
| Sample | The greybox chain: `greybox_gate`, `greybox_chapel`, `greybox_courtyard`, the one part `greybox` in `content/chapters.json` |

## Quick start

```sh
S=<path to this skill>
$S/scripts/new_game.sh ~/projects/mygame "My Game"   # copies template/ and templates/, sets the name
cd ~/projects/mygame
$S/scripts/fetch_addons.sh .                         # Dialogue Manager 4.1.0 and GUT 9.7.1, pinned
tools/godot.sh --version                             # must print 4.7.2.stable
tools/test.sh                                        # import, GUT, lint: "== ALL PASSED"
tools/build/export.sh macos
"build/macos/My Game.app/Contents/MacOS/My Game" -- --qa=greybox --qa-out="$PWD/docs/qa/001"
tools/build/export.sh web && bun tools/build/serve.ts &   # then:
bun tools/build/browser-qa.ts greybox
```

The game is set up when the greybox chain prints `RESULT PASS` in the
exported desktop app and in Chrome.

## Roles

| Who | Does |
|---|---|
| **Claude** | Everything in the repository: code, scenes, tools, image requests and processing, rigging and animation, audio, docs and plans. Picks its recommended option for routine art and technical choices, and records the pick and why. |
| **Operator** | Story, budgets, spend, and anything outside the repository (accounts, keys, stores, publishing). Reviews results and can overrule any pick. |

"Operator approval required" means "show the operator", not "wait", unless the
item is story, money or outside the repo.

## The production map

1. **Set up:** this skill, then plan 001 in `plans/`.
2. **Images:** [art-requests](../art-requests/SKILL.md) for every picture.
3. **Look:** [look-gate](../look-gate/SKILL.md), with one room proven in the
   engine before any volume art.
4. **Story:** [story-track](../story-track/SKILL.md): bible, cast, atlas, then
   a puzzle chart per part before its art.
5. **Per part:**
   - script and chart;
   - the area's style key;
   - [paint-room](../paint-room/SKILL.md) in batches of three or four;
   - [skinned-npc](../skinned-npc/SKILL.md);
   - close-ups and items;
   - [memory-reveals](../memory-reveals/SKILL.md) if the game has two-state
     places;
   - the part's playthrough in both builds.
6. **Hero:** [painted-hero](../painted-hero/SKILL.md) any time after the look
   gate.
7. **Voice:** [voice-cast](../voice-cast/SKILL.md) once the script is signed.
8. **Proof:** [ship-check](../ship-check/SKILL.md) after every slice.

## First-session checklist

1. Toolchain present: Godot 4.7.2 and its export templates, Bun, uv with
   Python 3.12, Codex CLI, ffmpeg, Chrome, and Blender 4.5 LTS for the hero.
2. `new_game.sh` ran, `fetch_addons.sh` ran, and `tools/godot.sh --version` is
   4.7.2.stable.
3. `git init -b main`, `git lfs install --local`, and the template's
   `.gitattributes` and `.gitignore` are in place before the first commit.
4. The operator writes `.env` (`AI_GATEWAY_API_KEY`, `ELEVENLABS_API_KEY`).
   Agents never write, print or commit it.
5. `tools/test.sh` passes, and `--qa=greybox` passes in the macOS app and in
   Chrome. Evidence goes in `docs/qa/001/`.
6. Fill the `{{PLACEHOLDER}}` prompts in `AGENTS.md`, `docs/game-design.md`
   and `docs/decisions.md` with the operator: the name, genre, tone, look and
   platforms.
7. Append the first entry to `docs/agent-board.md` (UTC), and mark plan 001
   in `plans/README.md`.
8. Next: [look-gate](../look-gate/SKILL.md).
