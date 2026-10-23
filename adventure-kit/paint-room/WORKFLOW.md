# paint-room workflow

Run everything from the repository root. The example room is
`harbour_steps`; replace it with yours. Room ids are `snake_case`.

## 0. Once per machine

```sh
(cd tools/art && uv sync --extra depth)     # the depth model adv-art room uses
tools/adv-art --help                         # align, grade, grid, overlay, room, closeup, icons, …
```

## 1. The now image

Write the request specs next to the room's data, from
[templates/requests.json](templates/requests.json). The `fields` fill the
`now` preamble's `{placeholders}` in `art-source/style/prompts/now.txt`; read
that file for its field names.

```sh
mkdir -p art-source/work/rooms/harbour_steps
bun tools/images/new-request.ts art-source/work/rooms/harbour_steps/requests.json   # prints IMG-#### harbour-steps-now
bun tools/images/run.ts IMG-0042                                                   # Sol, 3 variants, $0
```

Look at every variant. Check them against the request's acceptance criteria
and the composition rules (RULES.md 4). Record the verdict in the request's
Review table: `accepted: v2` and why, or `status: revise` with numbered notes
and run it again ([art-requests](../art-requests/SKILL.md)).

## 2. The then image

Write a `then` spec from [templates/then-request.json](templates/then-request.json)
whose only reference is the accepted now raw, then run it. The fields fill
`art-source/style/prompts/then.txt`.

```sh
bun tools/images/new-request.ts art-source/work/rooms/harbour_steps/then-request.json
bun tools/images/run.ts IMG-0043
```

## 3. The alignment gate

```sh
tools/adv-art align \
  --fixed  art-source/raw/IMG-0042/IMG-0042-v2.png \
  --moving art-source/raw/IMG-0043/IMG-0043-v1.png \
  --report art-source/work/rooms/harbour_steps/then_alignment.json
```

It prints the registration (scale, rotation, offset, `residual_p90_px`) and
`passes`, and exits 1 above 3 px (`--max-p90` changes the gate only with a
recorded decision). Try each variant and accept the best one that passes. If
none passes, revise. After two failed Sol rounds, set the request's model to
`openai/gpt-image-2.5-sunburst` with `size` `2560x1440` and run it through the
gateway (it costs money: check the plan's budget first).

## 4. Trace the room

```sh
mkdir -p build/trace
tools/adv-art grid --in art-source/raw/IMG-0042/IMG-0042-v2.png --out build/trace/harbour_steps_grid.png
```

Open the grid image. Copy [templates/room.json](templates/room.json) to
`art-source/work/rooms/harbour_steps/room.json` and fill it in, reading the
coordinates off the grid (every 100 px, red every 500):

- `walk`: the floor's outline, clockwise, kept off walls and furniture;
- `scale_zones`: the y and scale of the farthest and nearest walkable lines;
- `markers`: `default` plus one `from_<room>` per way in;
- `hotspots`: an outline, a `walk_to` point on the floor in front of it, and
  `exit` for ways out;
- `effects`: `preset`, and the key light's position and angle.

Every field is in [references/room-json.md](references/room-json.md). Then draw
it back onto the image and look at it:

```sh
tools/adv-art overlay --room art-source/work/rooms/harbour_steps/room.json --out build/trace/harbour_steps_overlay.png
```

Green is the walk area, yellow the hotspots, red the exits, dots the
`walk_to` points, magenta crosses the markers. Fix and redraw until it's
right.

## 5. Build

```sh
tools/adv-art room art-source/work/rooms/harbour_steps/room.json
```

It writes `content/rooms/harbour_steps/art/` (`bg_now.png`, `bg_then.png`,
`depth_now.png`, props and occluders) and
`art-source/work/rooms/harbour_steps/room_spec.json`. The report gives
`walk_area_luminance_now` (mean, median, p10, p90 from 0 to 255) and
`then_alignment_p90_px`. Compare the luminance with the area's style key; a
walk band much darker than the key's will swallow a dark hero.

```sh
tools/godot.sh --headless --import
tools/godot.sh --headless --script res://addons/adv_tools/new_room.gd -- \
  harbour_steps art-source/work/rooms/harbour_steps/room_spec.json --replace
```

`--replace` is needed whenever the scene exists. The script
`content/rooms/harbour_steps/harbour_steps.gd` is written only the first time.

## 6. The room script and its lines

Start from [templates/room_script.gd](templates/room_script.gd). Methods are
named `<verb>_<hotspot_id>`:

| Method | When it runs |
|---|---|
| `look_<id>()` | Look, the default click. Every hotspot needs one. |
| `use_<id>()`, `talk_<id>()` | Use and Talk from the verb coin, or the click when it is the hotspot's `default_verb` |
| `item_<id>(item: ItemDef)` | An inventory item used on the hotspot. Fall back with `Say.fallback(&"item")`. |
| `locked_<exit_id>()` | A click on an exit whose `requires_flag` isn't set |
| `_on_enter(from)` | Loaded, before it shows: set props and hotspots from flags here |
| `_on_shown()` | Visible: arrival lines and first-visit cutscenes |
| `_on_restore()` | After a save loads, instead of the two above |

Lines are `await Say.line(&"<part>/<file>", &"<cue>")`. The cues go in
`content/dialogue/<part>/<file>.dialogue`, each line with a static `[ID:…]`
([story-track](../story-track/SKILL.md)).

## 7. Register and prove

Add the room to its part's `rooms` in `content/chapters.json`. If it is the
part's first room, set the part's `start` to it.

```sh
tools/test.sh                                        # import, GUT (test_rooms_all) and the lint
tools/godot.sh -- --qa=rooms --rooms=harbour_steps --qa-out=build/qa/harbour_steps
tools/godot.sh -- --qa=rooms --part=<part_id> --qa-out=build/qa/<part_id>   # the whole part, with its flags set
```

The tour prints one `[qa] ROOM {…}` line a room (load ms, video MiB, frame
times), shoots `<room>_now.png` and `<room>_then.png`, looks at every visible
hotspot, and exits non-zero on a failed check. Look at the screenshots. The
gate in the exported build is [ship-check](../ship-check/SKILL.md)'s.

## Close-ups

1. Request it with the `closeup` preamble, the room's accepted now raw as the
   reference. Writing meant to be read goes in the prompt in quotes and is
   checked letter by letter in review.
2. Copy [templates/closeup.json](templates/closeup.json) to
   `art-source/work/closeups/<id>/closeup.json`. Trace its hotspots on
   `adv-art grid --in <raw>`.
3. Build the art and spec, write the script, then the scene:

```sh
tools/adv-art closeup art-source/work/closeups/tide_ledger/closeup.json
# write content/closeups/tide_ledger/tide_ledger.gd first: extends Closeup, look_<id>(), _on_shown()
tools/godot.sh --headless --import
tools/godot.sh --headless --script res://addons/adv_tools/new_closeup.gd -- \
  tide_ledger art-source/work/closeups/tide_ledger/closeup_spec.json --replace
```

4. Open it from the room: `await Closeups.open(&"tide_ledger", hotspots.get_node(^"Ledger") as Hotspot)`.
   It pushes in from the hotspot (decision #33), and a right-click, Esc or
   the back glyph closes it.
5. Add the id to the part's `closeups` in `content/chapters.json`.

## Items

1. One request per part with the `items` preamble, `background:
   transparent`, every object listed in reading order.
2. Cut the accepted sheet. Names come first, `--colour` last:

```sh
tools/adv-art icons --sheet art-source/raw/IMG-0050/IMG-0050-v1.png \
  brass_key tide_chart lamp_oil wet_rope --colour lamp_oil
```

3. Write `art-source/work/items/<part>.json` from
   [templates/items.json](templates/items.json), then:

```sh
tools/godot.sh --headless --import
tools/godot.sh --headless --script res://addons/adv_tools/new_item.gd -- art-source/work/items/<part>.json
```

4. The item's Look line is `look_file` / `look_cue` in a dialogue file. Give
   and take them in room scripts with `Inventory.add(&"brass_key")`,
   `Inventory.remove(…)` and `Inventory.has(…)`, after
   `await Rooms.player.play(&"pickup_high")` (or `pickup_low`, `use`,
   `give`).

## Props and clean plates

1. Request the clean plate as an edit of the accepted now raw: the same
   picture with the prop removed ("raw" kind, the now raw as the reference).
   Gate it with `adv-art align` like a then image.
2. In `room.json`, set `"plate": "<plate raw>"` and
   `"props": {"Crate": [[x, y], …]}`. Each prop is cut from the full now
   image as `prop_crate.png` and layered at `Layers/Now/Crate`.
3. In `_on_enter`, hide the layer and its hotspot once taken:
   `layers.get_node(^"Now/Crate").visible = not taken` and the same for
   `hotspots.get_node(^"Crate")`.
