# 🪓 Orc Skills

> **WAAAGH!** Battle-ready agent skills, forged by [TheOrcDev](https://github.com/TheOrcDev).

Blunt tools for warchiefs who want work done. Install through the Skills CLI for any supported agent, or use the shadcn command to drop a skill into Claude Code. Zug zug.

## 🎮 Game development

Six skills from the Final Stand production pipeline live in [`game-dev/`](game-dev/README.md), covering reference art, Meshy generation, Blender cleanup, animation and Unity integration. These workflows depend on Final Stand's project tooling and contracts; the collection documents those prerequisites.

| Skill | Purpose |
|---|---|
| [game-art-reference-packs](game-dev/game-art-reference-packs/SKILL.md) | Consistent four-view references, crop checks and source lineage |
| [meshy-asset-production](game-dev/meshy-asset-production/SKILL.md) | Geometry and texture tasks, credit accounting and original exports |
| [game-model-cleanup](game-dev/game-model-cleanup/SKILL.md) | Geometry repair, polygon budgets, materials and verified exports |
| [creature-animation](game-dev/creature-animation/SKILL.md) | Creature gaits, actions, deformation checks and preview reels |
| [humanoid-animation](game-dev/humanoid-animation/SKILL.md) | Meshy humanoid rigs, motion presets and equipment attachment |
| [unity-asset-integration](game-dev/unity-asset-integration/SKILL.md) | Native import, presentation assets and gameplay verification |
| [rig-it](game-dev/rig-it/SKILL.md) | Portable rigging and animation loop: contract, scaffold or Mixamo route, gates on a fresh reimport, reels, Blender scripts bundled |

Install a skill using its name, for example:

```bash
npx skills add TheOrcDev/skills --full-depth --skill game-art-reference-packs
```

The shadcn registry also includes each skill's workflow and rules files:

```bash
npx shadcn@latest add TheOrcDev/skills/game-art-reference-packs
```

### `rig-it` - game character rigging that survives the engine

Rigging is where past models hit the wall: one bpy script, an armature that binds, and no way to see the elbow is wrong. `rig-it` never lets the agent judge a rig from the code that built it. A per-subject contract picks the body plan; creatures get a deterministic scaffold rig and contact-driven Idle/Locomotion/Attack/Hit/Death clips, bipeds get a Mixamo-skeleton package (Meshy or mixamo.com) with rest-pose weight transfer, grip-seated weapons and polish passes that fix sliding feet, sinking deaths and hitching idles. Every clip is exported, **reimported into an empty scene**, measured against numeric gates, rendered over a checker floor and cut into a labeled reel. Unity Humanoid and Generic import documented. Blender 4.5 headless scripts included.

```bash
npx skills add TheOrcDev/skills --full-depth --skill rig-it
```

```bash
npx shadcn@latest add TheOrcDev/skills/rig-it
```

Call it with `/rig-it`, "rig this character", "my feet are sliding", or "get this Mixamo rig into Unity."

## 🗝️ Point-and-click adventure

Ten skills and a template project for making a mouse-driven, fully voiced point-and-click adventure in Godot 4.7.2, pulled out of the production of *Past* (52 painted rooms, 13 NPCs and a hand-painted hero, on desktop and in the browser). They live in [`point-and-click-adventure/`](point-and-click-adventure/README.md), with the production map.

| Skill | Purpose |
|---|---|
| [new-adventure](point-and-click-adventure/new-adventure/SKILL.md) | A working Godot project: adventure core, verb coin, inventory, saves, scaffolds, tools, tests, QA, desktop and web builds, a greybox sample that plays end to end |
| [art-requests](point-and-click-adventure/art-requests/SKILL.md) | Every image from a request file: Sol through Codex or GPT Image through the gateway, immutable raws, receipts, budgets |
| [look-gate](point-and-click-adventure/look-gate/SKILL.md) | Style bible, prompt preambles, style keys and one room proven in the engine before volume art |
| [story-track](point-and-click-adventure/story-track/SKILL.md) | Signed bible, cast and atlas, a puzzle chart per part before any art, scripts with line IDs, hints and playthroughs |
| [paint-room](point-and-click-adventure/paint-room/SKILL.md) | A playable room from one data file: present, aligned past, walk area, hotspots, close-ups, items |
| [painted-hero](point-and-click-adventure/painted-hero/SKILL.md) | The hero painted frame by frame by Sol over a Blender rig's pose guides |
| [skinned-npc](point-and-click-adventure/skinned-npc/SKILL.md) | Side characters as one painting skinned to a few bones |
| [memory-reveals](point-and-click-adventure/memory-reveals/SKILL.md) | Flashbacks, two-state rooms, cutscenes and zoom-out reveals |
| [voice-cast](point-and-click-adventure/voice-cast/SKILL.md) | Every line voiced with ElevenLabs, posted and wired to subtitles |
| [ship-check](point-and-click-adventure/ship-check/SKILL.md) | Proof in the exported desktop app and in Chrome, budgets, reels, deploys |

Start a game:

```bash
npx skills add TheOrcDev/skills --full-depth --skill new-adventure
```

Install the others the same way, and keep them side by side: they link to each other and `new-adventure` copies files from `painted-hero` and `look-gate`.

## 🎬 Video

Skills for scripting and packaging video content live in [`videos/`](videos/README.md), one folder per format. Short format is here now; long format and other video skills will land in the same directory as they are written.

| Skill | Purpose |
|---|---|
| [short-format-video](videos/short-format-video/SKILL.md) | Shorts, Reels and TikTok scripts: spoken script plus editor-ready shot list on the Hook, bridge, Value, CTA arc |

### `short-format-video` - Shorts scripts with editor-ready shot lists

Writes a TikTok, Reel or YouTube Short as one document with two halves: the **spoken script** and a beat-by-beat **shot list** (camera angle, captions, on-screen graphics, B-roll, cut notes), so an editor can cut the video from the doc and the footage alone. Every Short runs the same arc, **Hook, post-hook bridge, Value, CTA**, with a hard angle change right after the hook, captions on every beat, graphics that match the spoken line, and A-roll/B-roll marked per beat. Ships with the standing OrcDev packaging: four titles with one Recommended, description, X post, YouTube tags, and honest product claims only.

```bash
npx skills add TheOrcDev/skills --full-depth --skill short-format-video
```

```bash
npx shadcn@latest add TheOrcDev/skills/short-format-video
```

Call it with `/short-format-video`, "write a Short", or "script this Reel."

## 🪓 The Horde

### `orc-me` - orc voice mode

Makes Claude blunt, decisive, no hedging. Leads with the answer, picks a side, cuts the padding - but keeps every command and code path exactly right. The voice is the delivery; **directness is the weapon**.

```bash
npx shadcn@latest add TheOrcDev/skills/orc-me
```

Wake it with `/orc-me`, "orc mode", or "talk like an orc." Say "normal mode" to stand it down.

### `war-boss-review` - orc code review

Blunt, zero-hedging review of your changes. Ranks every finding **KILL IT** (blocker), **WEAK** (minor), or **WAAAGH-WORTHY** (strong), strips the politeness padding, and forces a verdict: ship or hold the line.

```bash
npx shadcn@latest add TheOrcDev/skills/war-boss-review
```

Call it with `/war-boss-review`, "orc review", or "roast my code."

### `cut-it` - plan slicer

Takes a plan you already have and cuts it into ordered, self-contained slices - execution phases sized for an AI agent to pick up and run one at a time. Dependency-ordered, each slice verifiable and safe to commit.

```bash
npx shadcn@latest add TheOrcDev/skills/cut-it
```

Call it with `/cut-it`, "slice this plan", or "break this into phases."

### `auto-grill` - self-driving plan grill

Grills a plan one question at a time, but drives the interview itself: each question gets three answers (**A/B/C**) with one marked **✅ Recommended**, and it auto-answers with the recommended pick - looping down the decision tree until the plan is fully resolved. Review every auto-made decision in one pass and flip any you disagree with.

```bash
npx shadcn@latest add TheOrcDev/skills/auto-grill
```

Call it with `/auto-grill`, "auto-grill this plan", or "grill it and decide."

### `shadscan-pre-commit` - AI agent commit check

Makes an AI agent establish a Shadscan baseline when work begins and audit again immediately before every agent-created commit. It does not install project dependencies, edit package scripts, or configure Git.

Install for Codex, Claude Code, Cursor, and other supported agents:

```bash
npx skills add TheOrcDev/skills --skill shadscan-pre-commit
```

Install into Claude Code through the shadcn registry:

```bash
npx shadcn@latest add TheOrcDev/skills/shadscan-pre-commit
```

Call it with `$shadscan-pre-commit`, "run Shadscan before every agent commit", or "prevent UI regressions in this agent task."

### `agent-qa-testing` - browser tests with evidence

Run the requested browser flow and bring back the evidence. [agent-qa](https://github.com/vostride/agent-qa) combines natural-language testing with advanced memidex memory and self-improvement. This skill validates and selects existing tests, runs them within the agreed scope, and inspects results and memory. A dry run is selection; a completed verdict is evidence.

Install for supported agents:

```bash
npx skills add TheOrcDev/skills --skill agent-qa-testing
```

Install into Claude Code through the shadcn registry:

```bash
npx shadcn@latest add TheOrcDev/skills/agent-qa-testing
```

Call it with `$agent-qa-testing` or "verify this flow with agent-qa." Requires an installed agent-qa CLI; live runs also need its browser and model provider.

### `github-to-origin` - move a repo to Cursor Origin

Moves a repo from GitHub to Cursor Origin hosting and, critically, repoints Vercel so production keeps deploying. Covers the two traps that make this look done when it isn't: a synced repo is a *mirror* with GitHub still the source of truth, and installing the Vercel app on the Origin repo does not move the project that owns your domain.

```bash
npx shadcn@latest add TheOrcDev/skills/github-to-origin
```

Call it with `/github-to-origin`, "move this repo to origin", or "why isn't my Origin push deploying?"

### `intro-video` - remotion intros with ASR captions

Builds Remotion intros, reels, and brand films with remocn. Caption times come from ASR (`sherpa-onnx` + zipformer) - never from character-count guesses. Script for spelling, ASR for timing.

```bash
npx shadcn@latest add TheOrcDev/skills/intro-video
```

Call it with `/intro-video`, "make an intro", or "caption this reel."

### `living-backdrop` - one still image, a hero that breathes

Takes a single image and makes it live: the subject slides against the background with the pointer, breathes around the point where it leaves the frame, and the scene gets wind, cloud drift, a light pulse and dust. **Two depth-mapped layers in one shader** - no video, no 3D model. The bundled pipeline cuts the mask, paints the subject out of the background, estimates depth, upscales and packs the textures; the three.js component fades in over a server-rendered poster that doubles as the reduced-motion fallback. Built for the [orcdev.com](https://orcdev.com) hero.

```bash
npx skills add TheOrcDev/skills --skill living-backdrop
```

```bash
npx shadcn@latest add TheOrcDev/skills/living-backdrop
```

Call it with `/living-backdrop`, "make this image feel alive", or "add depth to my hero."

### `grond` - one word, everything to main

Say **GROND** once. The agent stages every change, writes a real commit message,
merges onto the default branch, pushes, and reports back in orc voice. The word
itself is the authorization, so it never stops to ask. It still refuses to force-push,
halts on secrets like `.env` or `*.pem`, backs out cleanly on a merge conflict, and
reports a rejected push as a rejected push.

```bash
npx shadcn@latest add TheOrcDev/skills/grond
```

Call it with `/grond`, "GROND", or "smash it to main."

---

**Lok'tar Ogar!** 🪓
