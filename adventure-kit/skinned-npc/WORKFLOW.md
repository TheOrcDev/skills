# skinned-npc workflow

Run everything from the repository root. The example NPC is `keeper`;
replace it with yours. Ids are `snake_case`.

## 1. The painting

Write the request spec from [templates/request.json](templates/request.json).
The `fields` fill the `npc` preamble's `{placeholders}` in
`art-source/style/prompts/npc.txt`; read that file for its field names.

```sh
mkdir -p art-source/work/characters/keeper
bun tools/images/new-request.ts art-source/work/characters/keeper/request.json   # prints IMG-#### npc-keeper
bun tools/images/run.ts IMG-0051                                                # Sol, 3 variants, $0
```

Sol gives a portrait image whatever the size says (Past's came out at
1024 × 1536). Review each variant against RULES.md 1 to 7 and record the
pick and why in the request's Review table
([art-requests](../art-requests/SKILL.md)).

## 2. Trace the rig

```sh
mkdir -p build/trace
tools/adv-art grid --native --in art-source/raw/IMG-0051/IMG-0051-v2.png --out build/trace/keeper_grid.png
```

`--native` keeps the painting at its own size, so the grid reads in the
painting's pixels. Copy [templates/npc.json](templates/npc.json) to
`art-source/work/characters/keeper/npc.json` and fill it in:

1. `painting`: the accepted raw.
2. `feet`: the point between the feet on the ground line.
3. `speech`: a point a little above the head, where subtitles appear.
4. `height`: how tall the NPC stands on screen at scale 1, in pixels.
   Compare it with the hero's height at the nearest walk line (Past: about
   480 px for the hero, 430 for a stocky NPC).
5. `bones`: `Base` first, then the parts that move. See
   [references/bones-and-motions.md](references/bones-and-motions.md).
6. `motions`: `idle`, `talk_a`, `talk_b`, and any one-shots the script
   needs.
7. `speaker`, `aliases`, `subtitle_color`.

## 3. Build

```sh
tools/adv-art npc art-source/work/characters/keeper/npc.json
```

It trims the painting to the figure plus an 8 px margin, scales it so the
figure is 1.5× its on-screen `height` (room for close-up push-ins), greys it
unless `keep_color`, and writes `content/characters/keeper/keeper.png` and
`art-source/work/characters/keeper/npc_spec.json`, with every point moved into
the texture's pixels and the painting's outline for clicks. The report gives
the texture size and the scale factor.

```sh
tools/godot.sh --headless --import
tools/godot.sh --headless --script res://addons/adv_tools/new_npc.gd -- art-source/work/characters/keeper/npc_spec.json
```

It writes `content/characters/keeper/keeper.tscn`: an `Actor` with a
`RigBody` named `Body`, the painting as a `Polygon2D` meshed on a `grid`-pixel
grid inside its alpha and skinned to a `Skeleton2D`. It prints the vertex,
triangle and bone counts.

## 4. Look at it move

```sh
tools/godot.sh -- --qa=npc --npc=keeper --qa-out=build/qa/npc_keeper
tools/godot.sh -- --qa=npc --npc=keeper --room=harbour_steps --marker=default --qa-out=build/qa/npc_keeper_room
```

The first stages the NPC enlarged on grey; the second stands it in a room at
a marker. It shoots `keeper_idle.png`, three frames of each loop while
speaking, and three of each one-shot. Look at every shot:

| You see | Fix in `npc.json` |
|---|---|
| A tear or a stretched seam at a joint | Move the bone's ends to the middle of the limb, or add a bone for the part that drags |
| The coat or body bends with the arm | The arm's bone runs too close to the body; move it out along the arm |
| A foot slides or lifts | A motion names `Base`, or a leg has a bone; keep the legs on `Base` |
| The whole figure wobbles | The sway amplitudes are too big, or every bone has the same phase |
| Talk looks like idle | Raise the `voice` bends (Past used 4 to 16 degrees) |

Rebuild with `adv-art npc`, import and `new_npc.gd` after every change.

## 5. Place it and give it lines

In the room's `room.json` ([paint-room](../paint-room/SKILL.md)):

```json
"npcs": [{"scene": "res://content/characters/keeper/keeper.tscn", "name": "Keeper",
          "position": [1270, 880], "facing": "left", "era": "now"}],
"hotspots": [{"id": "keeper", "name": "Harbour keeper", "polygon": [[1180, 880], [1180, 460], [1360, 460], [1360, 880]],
              "walk_to": [1060, 900], "default_verb": "talk", "pick_priority": 2}]
```

Rebuild the room (`adv-art room`, `new_room.gd --replace`). In the room
script, `look_keeper()` and `talk_keeper()` say lines whose speaker is
`Keeper` (or an alias). For a gesture:

```gdscript
var keeper := actors.get_node_or_null(^"Keeper") as Actor
if keeper:
	await keeper.play(&"lean")
```

Add `keeper` to the part's `characters` in `content/chapters.json`, then run
`tools/test.sh` and `tools/godot.sh -- --qa=rooms --rooms=harbour_steps`.
