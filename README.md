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
