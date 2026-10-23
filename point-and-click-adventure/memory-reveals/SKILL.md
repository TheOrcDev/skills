---
name: memory-reveals
description: Adds a point-and-click adventure's two-state places and cinematics in a point-and-click-adventure Godot game. A room's past (or any second state) is an aligned edit of its present, carried in the same scene and switched in place; visions play the past as a skippable cutscene; playable memories hold the player in the past until a clue is found; memory vistas and discovery reveals pull back through a zoom stack of 3:1 rings with a title. Also covers the cutscene runner (walk, say, anim, shot, fade, era steps), letterbox, skipping that leaves the world as a watched run would, journal rewatching and Reduce camera motion. Use when the user wants a flashback, a memory, a vision, a past or alternate version of a room, a cutscene, an opening, a zoom-out reveal of a new area, a title card, or mentions Flashback, Vision, enter_memory, RevealCutscene, reveal.json, new_reveal.gd, adv-art reveal, rings, letterbox or rewatch.
---

# memory-reveals

The kit's places can have two states: the present the player walks, and a
past (or a dream, a future, a before and after) that comes back in the same
spot. Because the second state is an edit of the first, aligned to the pixel,
it can bloom out of the thing the player touched while the hero stays where
they stood. Past built its whole story on this ("memory is colour"): visions,
playable memories, memory vistas and a zoom-out reveal for each new area.

The module is optional. A game without a second state skips the eras and
still gets the cutscene runner and the reveals.

Read [RULES.md](RULES.md) first. Commands are in [WORKFLOW.md](WORKFLOW.md).
The cutscene steps are in
[references/cutscenes.md](references/cutscenes.md).

## The four kinds

| Kind | What the player sees | Call |
|---|---|---|
| Vision | The past blooms out of the clicked thing, plays a few lines, drains back. Watched, skippable | `Cutscenes.play(Vision.new(id, room, anchor, during))` |
| Playable memory | The past blooms in and stays: its walk area and hotspots, exits shut, until a clue is found | `Flashback.enter_memory(id, room, anchor, done_flag)` |
| Memory vista | A reveal's pull-back under the past's warm grade | `Cutscenes.play(RevealCutscene.new(id, stage, &"then"))` |
| Discovery reveal | On first arrival in an area: hold on the hero, pull back over the area, title | `Cutscenes.play(RevealCutscene.new(id, stage))` |

Every kind records its memory id when it ends, watched or skipped, and can be
watched again from the journal through the room's `rewatch_<id>()`.

## The loop

```
puzzle chart names the memory -> then-edit of the room (paint-room, align p90 <= 3 px)
   -> room script: vision / enter_memory + rewatch_<id>() -> journal entry
reveal: ring 0 (gateway, 3:1) -> adv-art reveal --sources -> ring 1, ring 2 (2x repaints)
   -> adv-art reveal -> new_reveal.gd -> RevealCutscene in the room -> --qa=reveals
```

## Quick start

```sh
# a vision in an existing two-era room: write the room script (WORKFLOW §2), then
tools/test.sh && tools/godot.sh -- --qa=journal --qa-out="$PWD/build/qa/journal"
# a discovery reveal
cp <skill>/templates/reveal.json art-source/work/reveal/harbour_reveal/reveal.json
tools/adv-art reveal --sources art-source/work/reveal/harbour_reveal/reveal.json
tools/adv-art reveal art-source/work/reveal/harbour_reveal/reveal.json
tools/godot.sh --headless --import
tools/godot.sh --headless --script res://addons/adv_tools/new_reveal.gd -- \
  --spec=art-source/work/reveal/harbour_reveal/reveal_spec.json \
  --out=res://content/cutscenes/harbour_reveal/harbour_reveal.tscn --title="THE HARBOUR" --place="The old port"
tools/godot.sh -- --qa=reveals --qa-out="$PWD/build/qa/reveals"
```

## Per-memory checklist

1. The memory is in the part's puzzle chart, and the clue it gives is needed.
2. The room's then image aligned at p90 ≤ 3 px (`adv-art align`).
3. The room script has the verb that starts it and `rewatch_<id>()`.
4. `content/journal/entries.gd` has its page (`MEMORIES`) and rewatch
   (`REWATCH`); `journal.dialogue` has its line.
5. Skipping it leaves the same flags, items and position as watching it.
6. It plays with Reduce camera motion on (a crossfade, no zoom).
7. Rings registered at p90 ≤ 3 px; no seam at 1080p or at full zoom.
8. `--qa=journal` (memories) or `--qa=reveals` passes in both builds.

## Next

Proof in both builds: [ship-check](../ship-check/SKILL.md). The lines spoken
inside memories: [voice-cast](../voice-cast/SKILL.md).
