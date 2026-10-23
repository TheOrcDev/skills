---
name: paint-room
description: Turns an atlas entry into a playable room in an adventure-kit Godot project. The present image comes from Sol, the past image is an edit of it, an alignment gate checks the pair, and a traced room.json is built with adv-art room and the new_room.gd scaffold, then hotspot lines and the every-room test. Also makes the room's close-ups, inventory items, props and clean plates. Use when building or rebuilding a room, tracing a walk area, hotspots, exits or markers, adding a room's past version, making a close-up of something in a room, cutting an item sheet into inventory icons, or making something the player can take away. Also use when the user mentions room.json, room_spec.json, new_room.gd, adv-art room, align, grid, overlay, closeup.json, new_closeup.gd, item icons, new_item.gd, props or a clean plate.
---

# paint-room

A room is one data file. `room.json` names the accepted images and traces the
walk area, scale zones, markers, hotspots, exits, props and effects in screen
pixels. One command builds the art and a spec from it, and one Godot script
builds the scene from that spec. Nobody hand-assembles a `.tscn`. Past built
50 rooms this way, with every past version aligned on its first round.

Read [RULES.md](RULES.md) before the first request. Run the commands in
[WORKFLOW.md](WORKFLOW.md) as written. Every field is in
[references/room-json.md](references/room-json.md).

## The loop

```
atlas entry -> now request (Sol) -> accept -> then request (edit of the now) -> align, p90 <= 3 px
   -> room.json traced on `adv-art grid`, checked on `adv-art overlay`
   -> adv-art room -> godot --import -> new_room.gd -> room script and lines
   -> content/chapters.json -> tools/test.sh (test_rooms_all) -> --qa=rooms --rooms=<id>
```

1. **Request the now image** through [art-requests](../art-requests/SKILL.md),
   with the `now` preamble and the area's style key as the reference. The
   room's composition notes come from the atlas: floor, exits, hotspots.
2. **Accept one variant** and write why in its Review table.
3. **Request the then image** as an edit of the accepted now (`then`
   preamble, the now raw as the only reference). Skip it if the room has no
   past.
4. **Gate the pair:** `tools/adv-art align`. A p90 above 3 px is a revise
   round. After two Sol misses, the gateway's Sunburst makes the edit.
5. **Trace `room.json`** on `adv-art grid`, then draw it back with
   `adv-art overlay` and look at the overlay before building.
6. **Build:** `adv-art room` writes `content/rooms/<id>/art/` and
   `room_spec.json`. Import, then run `new_room.gd`. It writes the room
   script once and never overwrites it. `--replace` rebuilds the scene.
7. **Write the room script:** a `look_<id>()` for every hotspot, the default
   verb's method, `item_<id>(item)` where items apply, and `locked_<exit>()`
   for exits that need a flag. The lines go in the part's dialogue file
   ([story-track](../story-track/SKILL.md)).
8. **Register** the room in its part in `content/chapters.json`.
9. **Prove it:** `tools/test.sh`, then `--qa=rooms --rooms=<id>`, which shows
   both eras, looks at every hotspot and measures load time, frame time and
   video memory.

## Quick start

```sh
bun tools/images/new-request.ts art-source/work/rooms/harbour_steps/requests.json   # now (and then, next round)
bun tools/images/run.ts IMG-0042
tools/adv-art align --fixed art-source/raw/IMG-0042/IMG-0042-v2.png \
  --moving art-source/raw/IMG-0043/IMG-0043-v1.png --report art-source/work/rooms/harbour_steps/then_alignment.json
tools/adv-art grid --in art-source/raw/IMG-0042/IMG-0042-v2.png --out build/trace/harbour_steps_grid.png
tools/adv-art overlay --room art-source/work/rooms/harbour_steps/room.json --out build/trace/harbour_steps_overlay.png
tools/adv-art room art-source/work/rooms/harbour_steps/room.json
tools/godot.sh --headless --import
tools/godot.sh --headless --script res://addons/adv_tools/new_room.gd -- harbour_steps art-source/work/rooms/harbour_steps/room_spec.json --replace
tools/test.sh
tools/godot.sh -- --qa=rooms --rooms=harbour_steps --qa-out=build/qa/harbour_steps
```

## Per-room checklist

1. The now image follows the composition rules: open floor in the lower 30
   to 40%, the walk band against mid-to-light fog, 3 to 6 hotspots, no
   people, no text.
2. The then image aligns at p90 ≤ 3 px (`then_alignment.json` says `passes`).
3. The overlay shows the walk polygon on the floor, every hotspot on its
   object, every `walk_to` inside the walk area, and a `default` marker.
4. Every exit names a room and an entry marker that exists there.
5. `adv-art room` reports the walk area's luminance, and a screenshot of the
   hero at the walk band's darkest spot still reads.
6. `tools/test.sh` passes: every hotspot answers Look, every exit lands.
7. `--qa=rooms` passes: under 400 MiB of video memory, under 1 s to load,
   frame p95 under 16.7 ms. Screenshots of both eras are looked at.

## Details in the same room

| Detail | Data | Build | Scene |
|---|---|---|---|
| Close-up | `art-source/work/closeups/<id>/closeup.json` | `adv-art closeup` | `new_closeup.gd`, opened by `Closeups.open(&"<id>", hotspot)` |
| Inventory items | one Sol item sheet per part, `art-source/work/items/<part>.json` | `adv-art icons --sheet … [--colour …] <names>` | `new_item.gd` |
| Props | `plate` and `props` in `room.json` | `adv-art room` cuts each prop as a layer | the room script hides the layer and its hotspot |

## Next

- People in the room: [skinned-npc](../skinned-npc/SKILL.md).
- A memory, a vision or a discovery reveal here: [memory-reveals](../memory-reveals/SKILL.md).
- After each batch of three or four rooms: [ship-check](../ship-check/SKILL.md).
