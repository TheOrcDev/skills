# memory-reveals workflow

Run everything from the repository root. `<skill>` is this skill's folder.

## 1. A room with a past

The second state is part of the room, built by [paint-room](../paint-room/SKILL.md):

1. Request the then image as an edit of the accepted now image, with the
   `then` preamble (`keep`, `place`, `when`, `restore`).
2. Gate it:

   ```sh
   tools/adv-art align --fixed art-source/raw/IMG-0042/IMG-0042-v2.png \
     --moving art-source/raw/IMG-0043/IMG-0043-v1.png --report build/align/harbour_steps.json
   ```

   Exit 0 and `residual_p90_px` ≤ 3 pass. Otherwise revise the request.
3. Name it as `then` in `room.json`. Hotspots that exist only in one era get
   `"era": "then"` or `"era": "now"`; a different walk area in the past goes in
   `walk_then`. `adv-art room` aligns the then image and cuts occluders in both
   eras; `new_room.gd` tags every layer, walk area and hotspot with its era.

Check both eras with `tools/godot.sh -- --qa=rooms --rooms=<id>`: it shoots the
room now and then.

## 2. A vision or a playable memory

1. In the room script, write the verb that starts it and `rewatch_<id>()`
   ([references/cutscenes.md](references/cutscenes.md) has both shapes).
2. Lines spoken inside it go in the room's dialogue file, with `[ID:…]` and
   `[#vo=…]` like any other.
3. In `content/journal/entries.gd`:

   ```gdscript
   const MEMORIES := {
   	&"statue_hand": {"title": "The saint's hand", "cue": &"statue_hand"},
   }
   const REWATCH := {
   	&"statue_hand": {"title": "The saint's hand", "room": &"harbour_chapel"},
   }
   ```

   and the cue `statue_hand` in `content/dialogue/journal.dialogue`.
4. If the memory is a hint goal, add `{"goal": &"…", "memory": &"statue_hand"}`
   to `content/hints/goals.gd`.
5. In the part's playthrough, `await _verb("Statue", &"use")` then
   `await _until_memory(&"statue_hand")`.

## 3. A cutscene

Write `content/cutscenes/<id>/<id>.gd` extending `Cutscene` (shape in
[references/cutscenes.md](references/cutscenes.md)). Play it from a room with
`await Cutscenes.play(...)`, or make it the opening by setting `opening` on the
`Main` node in `src/core/main.tscn` to its script path. An opening ends on
black: `main.gd` starts the first room behind it and clears the fade.

## 4. A discovery reveal

1. **Ring 0:** a gateway request (Flare), `size` `3072x1072`, quality high,
   with the area's style key as the reference. The prompt describes the whole
   area from one high viewpoint and names a lit, empty landing where the hero
   stands.

   ```sh
   bun tools/images/run.ts IMG-0070
   ```

2. **The data file:**

   ```sh
   mkdir -p art-source/work/reveal/harbour_reveal
   cp <skill>/templates/reveal.json art-source/work/reveal/harbour_reveal/reveal.json
   ```

   Set `ring0` to the accepted raw and `feet` to the landing, in ring 0's
   pixels (trace on `tools/adv-art grid --native --in <ring0> --out build/trace/ring0.png`).
   Leave `ring1` and `ring2` out for now.
3. **Ring 1:**

   ```sh
   tools/adv-art reveal --sources art-source/work/reveal/harbour_reveal/reveal.json
   ```

   It writes `ring1_source.png`: the 1536×536 crop round the hero's spot,
   scaled to 3072×1072. Request ring 1 from the gateway's Sunburst with that
   file as the reference: "a crop from a wide painting … repaint it as a
   full-resolution painting of the same view, keep every shape where it is,
   add the detail a closer view shows". Accept, set `ring1`, run `--sources`
   again for `ring2_source.png`, and repeat for ring 2.
4. **Build:**

   ```sh
   tools/adv-art reveal art-source/work/reveal/harbour_reveal/reveal.json
   ```

   It registers each ring on the one outside it (the report prints each
   ring's `residual_p90_px`; above 3, revise that ring), grades them, and
   writes `content/cutscenes/harbour_reveal/art/ring*.png` and
   `reveal_spec.json`.
5. **The scene:**

   ```sh
   tools/godot.sh --headless --import
   tools/godot.sh --headless --script res://addons/adv_tools/new_reveal.gd -- \
     --spec=art-source/work/reveal/harbour_reveal/reveal_spec.json \
     --out=res://content/cutscenes/harbour_reveal/harbour_reveal.tscn \
     --title="THE HARBOUR" --place="The old port" [--replace]
   ```

   The scene holds the zoom stack, the hero standing at `feet`, the title card
   and a `reveal` animation (hold, pull back, title in, title out).
6. **Play it** from the area's first room (`_on_shown`, once) and give the room
   `rewatch_<id>()`; add it to the part's `cutscenes` in
   `content/chapters.json` and to `REWATCH` in the journal entries.

## 5. Check

```sh
tools/test.sh
tools/godot.sh -- --qa=reveals --qa-out="$PWD/build/qa/reveals"     # every reveal, shot at its key moments
tools/godot.sh -- --qa=vista --qa-out="$PWD/build/qa/vista"         # a reveal and its memory vista
tools/godot.sh -- --qa=journal --qa-out="$PWD/build/qa/journal"     # a memory seen, the journal, a rewatch
tools/godot.sh -- --qa=reduced_motion --qa-out="$PWD/build/qa/rm"   # crossfades instead of moves
tools/godot.sh -- --qa=skip --qa-out="$PWD/build/qa/skip"           # a held Skip fast-forwards
```

Then the same scenarios in the exported builds, with
[ship-check](../ship-check/SKILL.md).
