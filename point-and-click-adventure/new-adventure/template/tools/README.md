# tools

Command-line tools that run outside Godot. Godot ignores this folder
(`.gdignore`). Scripts that Godot itself runs live in `addons/adv_tools/`.
Run everything from the repository root, so Bun loads `.env`.

## Environment

| Variable | Used by | Default |
|---|---|---|
| `GODOT_BIN` | `godot.sh` and everything that calls Godot | `$HOME/Applications/Godot-4.7.2.app/Contents/MacOS/Godot` |
| `AI_GATEWAY_API_KEY` | `images/`, the gateway engine | none |
| `ELEVENLABS_API_KEY` | `audio/` | none |
| `BLENDER`, `HERO_BASE_MESH`, `HERO_RIG_CONFIG` | `build/build_hero.sh` | `/Applications/Blender.app/...`; the base mesh has no default |
| `VERCEL_SCOPE`, `VERCEL_PROJECT` | `build/deploy.sh` | none |

The operator puts secrets in `.env` at the repository root, which is
gitignored. Agents never write, print or commit `.env`.

## Layout

| Path | What |
|---|---|
| `godot.sh` | Runs the pinned Godot with any arguments; keeps `build/.gdignore` |
| `test.sh` | Headless import, GUT tests and content lint, logs in `build/test-logs/`. Exits non-zero on failure. |
| `adv-art` | The image processing CLI (`tools/art`, Python 3.12 through `uv`): `align`, `grade`, `mask`, `cut`, `ring`, `depth`, `sheet`, `pack`, `room`, `npc`, `painted`, `icons`, `closeup`, `reveal`, `grid`, `overlay`, `placeholder-hero`. `tools/adv-art <command> --help` |
| `images/` | Image requests (Bun + TypeScript): `run.ts IMG-#### [--dry-run]`, `new-request.ts specs.json`, `index.ts`, `check.ts`. Sol through Codex, or the Vercel AI Gateway; raws, receipts, the ledger and budgets (`budgets.json`) |
| `audio/` | The voice pipeline (Bun + TypeScript): `run.ts extract`, `diff`, `report`, `post [--force]` |
| `blender/` | The hero's pose rig (`pose_rig.py`, from the painted-hero skill) |
| `build/` | `export.sh macos|web`, `serve.ts`, `browser-qa.ts <scenario>`, `pck_list.py`, `deploy.sh [--prod]`, `build_hero.sh [--guides|--placeholder]`, `loading_art.sh [room]` |

## Tests

| Command | Covers |
|---|---|
| `tools/test.sh` | The Godot project: import, GUT, lint |
| `(cd tools/images && bun test)` | The image tool, against a fake `codex` and gateway |
| `(cd tools/audio && bun test)` | The voice tool (no network; `post` needs ffmpeg) |
| `(cd tools/art && uv run pytest)` | `adv-art` |

## Rebuilding the greybox

The sample chain's art is drawn in code, so nothing is generated or paid for:

```sh
uv run --project tools/art python art-source/work/greybox/build.py
tools/adv-art npc art-source/work/characters/warden/npc.json
tools/godot.sh --headless --import
for room in greybox_gate greybox_chapel greybox_courtyard; do
  tools/godot.sh --headless --script res://addons/adv_tools/new_room.gd -- $room art-source/work/rooms/$room/room_spec.json --replace
done
tools/godot.sh --headless --script res://addons/adv_tools/new_closeup.gd -- greybox_notice art-source/work/closeups/greybox_notice/closeup_spec.json --replace
tools/godot.sh --headless --script res://addons/adv_tools/new_npc.gd -- art-source/work/characters/warden/npc_spec.json
tools/godot.sh --headless --script res://addons/adv_tools/new_reveal.gd -- --spec=art-source/work/reveal/greybox_vista/reveal_spec.json \
  --out=res://content/cutscenes/greybox_vista/greybox_vista.tscn --title="BEYOND THE GATE" --place="The greybox" --replace
tools/build/build_hero.sh --placeholder
tools/godot.sh --headless --script res://addons/adv_tools/scaffold_core.gd -- --replace=hero
```

Delete the greybox (its rooms, items, dialogue, close-up, warden, vista,
`content/story/greybox_playthrough.gd`, its test and its part in
`content/chapters.json`) once the game's own first part plays.
