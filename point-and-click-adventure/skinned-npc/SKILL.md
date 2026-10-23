---
name: skinned-npc
description: Adds a talking side character to a point-and-click-adventure Godot game as one painting skinned to a few bones. Sol paints the NPC once on a transparent background, npc.json places 4 to 8 bones and the feet, adv-art npc trims and grades the painting, new_npc.gd meshes and skins it to a Skeleton2D, and RigBody plays motions written as data (idle sway, voice-driven talk bends, keyed one-shots). Use when adding, redesigning or re-rigging an NPC, a shopkeeper, a guard or any non-player character, when an NPC's arms tear or its feet slide, when giving an NPC a gesture such as lean, write or ring a bell, or when the user mentions npc.json, npc_spec.json, new_npc.gd, RigBody, motions, bones or a skinned painting.
---

# skinned-npc

An NPC is one painting and a data file. No frames are drawn and nothing is
rendered: the painting is meshed inside its alpha, skinned to a handful of
bones, and the bones sway, bend while the NPC speaks, and play keyed
gestures. Past made 13 NPCs this way, at about 15 minutes each once the
tools existed, and its first NPC took under 1 MiB of video memory. The
Blender route it replaced was estimated at 4 to 6 hours an NPC.

Read [RULES.md](RULES.md) before the request. Commands are in
[WORKFLOW.md](WORKFLOW.md). Bone placement and the motion format are in
[references/bones-and-motions.md](references/bones-and-motions.md).

## The loop

```
cast entry -> npc request (Sol, transparent) -> accept -> npc.json (feet, speech, bones, motions)
   -> adv-art npc -> godot --import -> new_npc.gd -> --qa=npc screenshots -> fix bones, rebuild
   -> room.json npcs + a talk hotspot -> chapters.json characters -> --qa=rooms
```

1. **Request** the painting through [art-requests](../art-requests/SKILL.md)
   with the `npc` preamble, `background: transparent`, and the area's style
   key as the reference. Describe a silhouette that reads by outline: hat,
   cloak, tool, posture.
2. **Accept** the variant whose arms and head stand clear of the body, so
   they can bend without dragging the coat along.
3. **Write `npc.json`** from [templates/npc.json](templates/npc.json), in the
   painting's own pixels: the feet, the speech point above the head, the
   on-screen height, and the bones from the feet up.
4. **Build:** `adv-art npc` trims the painting to 1.5× its on-screen height,
   greys it unless `keep_color`, and writes `npc_spec.json`. Then import,
   then `new_npc.gd`, which writes `content/characters/<id>/<id>.tscn`.
5. **Look at it move:** `--qa=npc --npc=<id>` shoots idle and every motion.
   Tears, a floating foot or a stiff arm mean a bone is in the wrong place:
   fix `npc.json` and rebuild. Nothing is edited in the scene.
6. **Place it:** an `npcs` entry and a hotspot with `default_verb: talk` in
   the room's `room.json` ([paint-room](../paint-room/SKILL.md)), and the id
   in the part's `characters` in `content/chapters.json`.
7. **Lines:** the dialogue speaker name is the NPC's `speaker` (or one of its
   `aliases`), so its subtitles sit at its speech point in its colour and its
   body acts each line.

## Quick start

```sh
bun tools/images/new-request.ts art-source/work/characters/keeper/request.json
bun tools/images/run.ts IMG-0051
tools/adv-art grid --native --in art-source/raw/IMG-0051/IMG-0051-v2.png --out build/trace/keeper_grid.png
# write art-source/work/characters/keeper/npc.json from templates/npc.json
tools/adv-art npc art-source/work/characters/keeper/npc.json
tools/godot.sh --headless --import
tools/godot.sh --headless --script res://addons/adv_tools/new_npc.gd -- art-source/work/characters/keeper/npc_spec.json
tools/godot.sh -- --qa=npc --npc=keeper --qa-out=build/qa/npc_keeper
```

## Per-NPC checklist

1. The painting is whole from head to feet, on real transparency, grey
   rather than black (a dark hero must read against it), with no text.
2. `npc.json` has a `Base` bone from the feet up, 4 to 8 bones in all, one
   down the middle of each part that should move, and `idle`, `talk_a` and
   `talk_b` motions.
3. `new_npc.gd` prints the vertex, triangle and bone counts. Past's first
   NPC: 285 vertices, 7 bones.
4. The `--qa=npc` shots show no tearing, the feet planted in every motion,
   and the talk motions visibly different from idle.
5. In its room: it stands on the walk band's floor at the right scale, its
   hotspot wins over whatever is behind it, and every line's speaker matches
   `speaker` or an alias.

## Next

- Back to the room that places it: [paint-room](../paint-room/SKILL.md).
- Its lines and voice direction: [story-track](../story-track/SKILL.md),
  then [voice-cast](../voice-cast/SKILL.md).
- The part's proof in both builds: [ship-check](../ship-check/SKILL.md).
