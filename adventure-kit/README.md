# Adventure kit

Ten skills and a template project for making a mouse-driven, fully voiced
point-and-click adventure with painted backgrounds, a hand-painted hero and
an agent doing the production. Built from Past, which went from an empty repo
to 52 playable rooms, 13 NPCs and a painted hero in every animation, on
desktop and in the browser. Its art cost $1.14 through the gateway: Sol made
the rest on a ChatGPT plan.

The kit is Godot 4.7.2 with GDScript, our own small adventure core and
Dialogue Manager 4. Images come from GPT-6.1 Sol through Codex, with the
Vercel AI Gateway (GPT Image) as the fallback. Voice comes from ElevenLabs.

## The production map

Load the skill for the step you are on. `new-adventure` sets up the game and
every skill names the one that follows it.

| Step | Skill | What comes out |
|---|---|---|
| 1. Set up | [new-adventure](new-adventure/SKILL.md) | A Godot project with the adventure core, scaffolds, tools, tests, QA, desktop and web exports, the docs skeleton and `AGENTS.md`. The greybox sample game plays end to end. |
| 2. Every image | [art-requests](art-requests/SKILL.md) | One request file per image, raws that are never edited, receipts, a ledger and a budget |
| 3. The look | [look-gate](look-gate/SKILL.md) | The style bible, the prompt preambles, the first style key and one room proven in the engine |
| 4. The story | [story-track](story-track/SKILL.md) | The bible, cast and atlas, then per part a puzzle chart, the script, hints, journal pages and a playthrough test |
| 5. Rooms | [paint-room](paint-room/SKILL.md) | Playable rooms in both eras, with close-ups, items and props |
| 6. The hero | [painted-hero](painted-hero/SKILL.md) | The main character painted frame by frame over a rig's poses |
| 7. NPCs | [skinned-npc](skinned-npc/SKILL.md) | Side characters as one painting each, skinned to a few bones |
| 8. Memories | [memory-reveals](memory-reveals/SKILL.md) | Flashbacks, two-state rooms, cutscenes and zoom-out discovery reveals (optional) |
| 9. Voice | [voice-cast](voice-cast/SKILL.md) | Every line voiced, posted and wired to the subtitles |
| 10. Proof | [ship-check](ship-check/SKILL.md) | Tests, QA in the exported desktop app and in Chrome, budgets, reels, deploy |

Per part of the game, the loop is: puzzle chart and script, the area's style
key, rooms in batches of three or four, NPCs, close-ups and items, memories,
then the part's playthrough in both builds.

## Requirements

| Tool | For | Notes |
|---|---|---|
| Godot 4.7.2 | everything | `GODOT_BIN`, or the default `$HOME/Applications/Godot-4.7.2.app` |
| Bun | `tools/images`, `tools/audio`, the browser QA | |
| uv with Python 3.12 | `tools/art` (`adv-art`) | The system Python may be too new for the depth model |
| Codex CLI on a ChatGPT plan | Sol, the default image engine | `codex exec` must run |
| `AI_GATEWAY_API_KEY` | the gateway image engine | In `.env`, never printed |
| Blender 4.5 LTS | the hero's pose rig | Plus Blender Studio's CC0 human base meshes |
| ffmpeg | voice post-processing, reels | |
| Chrome | the browser QA | |
| `ELEVENLABS_API_KEY` | voice | In `.env` |

## Install

```bash
npx skills add TheOrcDev/skills --full-depth --skill new-adventure
```

Install the whole collection the same way, one skill name at a time. Keep the
skills together: they link to each other by relative path.

## Names

The template uses generic names. A game renames what it wants after
`new-adventure` copies it.

| Name | What it is |
|---|---|
| `hero` | The main character: `content/characters/hero/`, `HeroBody` |
| `adv-art` | The image processing CLI (`tools/adv-art`, Python package `tools/art/adv_art`) |
| `addons/adv_tools/` | The Godot scaffolds: `new_room.gd`, `new_npc.gd`, `new_closeup.gd`, `new_item.gd`, `new_reveal.gd`, `import_sprites.gd`, `lint.gd`, `scaffold_core.gd` |
| `tools/images` | The image tool: `run.ts`, `new-request.ts`, `index.ts`, `check.ts` |
| `tools/audio` | The voice tool: `run.ts extract`, `diff`, `report`, `post` |
| `tools/build` | `export.sh`, `serve.ts`, `browser-qa.ts`, `pck_list.py`, `deploy.sh`, `build_hero.sh` |
| now / then | The two eras of a room: the present and the remembered past |
| style key | An area's first accepted room image, the reference for the rest of the area |
| part | A chapter, as listed in `content/chapters.json` |

## Where it came from

Past (2026-10) and its plans 001 to 010. The rules in each skill's `RULES.md`
are the ones that cost Past a rework. The numbers quoted are Past's.
