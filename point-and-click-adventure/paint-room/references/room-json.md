# Room data reference

Every coordinate is in room pixels: 1920 × 1080, origin top left, y down.
Polygons are lists of `[x, y]` points, in order, not closed. The builders are
`tools/art/adv_art/room.py` (`adv-art room`, `closeup`, `grid`, `overlay`),
`tools/art/adv_art/icons.py`, and the scaffolds in `addons/adv_tools/`.

## `room.json`

`art-source/work/rooms/<id>/room.json`. [templates/room.json](../templates/room.json)
is a typical room, and [templates/room.full.json](../templates/room.full.json)
uses every field.

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | The room id, `snake_case`. Art goes to `content/rooms/<id>/art/`. |
| `display_name` | yes | The name the game shows |
| `now` | yes | The accepted now raw, `art-source/raw/IMG-####/IMG-####-vN.png`. Resized to 1920 × 1080 and made monochrome. Its depth map drives the fog. |
| `now_grade` | no | `"keep"` keeps the now image's colour. Any other value, or none, makes it monochrome. |
| `then` | no | The accepted then raw. It is registered onto the now raw, warped into its frame and resized. Without it the room has no past. |
| `walk` | yes | The walk area's outline in the now era. It must bake into a navigation polygon, so keep it simple and not self-crossing. |
| `walk_then` | no | The walk area in the then era, when the past's floor differs. Defaults to `walk`. |
| `scale_zones` | yes | `far_y`, `far_scale`, `near_y`, `near_scale`. Actors scale linearly between the two lines. Past used 0.55 to 0.92 far and 0.66 to 1.05 near. |
| `markers` | yes | Name → `[x, y]`. `default` is required. Name entry points `from_<room>`. |
| `hotspots` | yes | A list; fields below |
| `npcs` | no | Characters placed among the actors; fields below |
| `plate` | no | A clean plate raw: the now image with the props removed. With it, the background is the plate and each prop is cut from the full now image. |
| `props` | with `plate` | Name → polygon. Each becomes `prop_<name>.png` and the layer `Layers/Now/<Name>`. |
| `occluders` | no | Name → polygon. Cut from both eras as walk-behind sprites. The baseline (where the hero passes behind) is the polygon's lowest point. |
| `effects` | yes | The room's living-painting effects; fields below |

### Hotspot

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | `snake_case`. The node is its PascalCase (`tide_board` → `TideBoard`), and the room script's methods are `<verb>_<id>`. |
| `name` | yes | The hover label |
| `polygon` | yes | The clickable outline |
| `walk_to` | yes | Where the hero stands to interact, inside the walk area |
| `default_verb` | no | What a plain click does: `look` (the default), `use` or `talk`. Exits default to `walk`. |
| `pick_priority` | no | Higher wins where hotspots overlap. Default 0. |
| `era` | no | `"now"` or `"then"` to answer in one era only |
| `exit` | no | Makes it an exit: `room` (the target), `entry` (a marker there, default `default`), `direction` (`left`, `right`, `up`, `down`: the cursor) and `requires_flag` (a story flag; until set, the room's `locked_<id>()` answers) |

### NPC placement

| Field | Meaning |
|---|---|
| `scene` | `res://content/characters/<id>/<id>.tscn`, built by [skinned-npc](../../skinned-npc/SKILL.md). Build the NPC before the room that places it. |
| `name` | The node name under `Actors`, used by the room script (`actors.get_node(^"Keeper")`) |
| `position` | Where the feet stand |
| `facing` | `"right"` (the painting as painted) or `"left"` (mirrored) |
| `era` | `"now"` or `"then"`, or leave it out for both |

The NPC also needs a hotspot over its outline, usually with `default_verb:
talk` and a `pick_priority` above whatever is behind it.

### Effects

| Field | Default | Meaning |
|---|---|---|
| `preset` | `exterior` | `exterior` (two fog bands and moonlight shafts), `interior` (fog, window shafts and ash) or `none` |
| `light` | `[1480, 120]` | Where the light shafts start |
| `aim` | `225` | The shafts' direction in degrees |
| `ground_mist` | `true` | A low mist band in the foreground (with a preset) |
| `then` | `true` | The warm set for the past: golden shafts, warm haze, golden dust (only with a `then` image) |
| `extra` | `[]` | More effects, written out: `type` (a global class: `FogLayer`, `LightShafts`, `DustMotes`), `name`, `era` (`now`, `then` or empty), `layer` (`background` or `foreground`) and `properties` (the class's exported properties; colours as `[r, g, b, a]`, vectors as `[x, y]`, `res://` paths as resources) |

## `room_spec.json` (written by `adv-art room`, read by `new_room.gd`)

Don't edit it; edit `room.json` and rebuild. It holds `display_name`,
`layers` (per era: `name`, `texture`, optional `position`), `walk` (per era),
`scale_zones`, `markers`, `hotspots` (as given), `occluders` (`name`, `era`,
`texture`, `rect`, `baseline`), `npcs`, and `effects` (each `type`, `name`,
`era`, `layer`, `properties`).

## The scene `new_room.gd` builds

```
<RoomId> (Node2D, script content/rooms/<id>/<id>.gd extends Room)
  Layers/      Now/, Then/      Sprite2D per layer, era effects
  WalkAreas/   Now, Then        NavigationRegion2D per era; only the room's era is enabled
  ScaleZones                    far and near lines
  Hotspots/                     Hotspot or Exit (Area2D + CollisionPolygon2D "Shape")
  Exits/                        empty; exits live under Hotspots
  Markers/                      Marker2D per marker
  Actors/                       y-sorted: the hero, NPCs, occluders
  Foreground/                   framing and foreground effects
  Cinematics/                   for a room's own AnimationPlayer and camera
```

Era-tagged nodes outside `Layers` and `WalkAreas` (occluders, NPCs,
foreground effects) are in the groups `era_now` and `era_then`, and
`Room.set_era()` shows only the current era's.

## `closeup.json`

`art-source/work/closeups/<id>/closeup.json`, built by `adv-art closeup` into
`content/closeups/<id>/art/bg.png` and `closeup_spec.json` for
`new_closeup.gd`.

| Field | Meaning |
|---|---|
| `id` | The close-up id. The scene is `content/closeups/<id>/<id>.tscn`. |
| `image` | The accepted raw. Resized to 1920 × 1080 and made monochrome. |
| `grade` | `"keep"` keeps its colour |
| `hotspots` | `id`, `name`, `polygon`, optional `default_verb` and `pick_priority`. No `walk_to`: nobody walks in a close-up. List small hotspots before the catch-all. |

The close-up's script, `content/closeups/<id>/<id>.gd`, `extends Closeup`,
answers `<verb>_<id>()`, and sets flags for legible writing in `_on_shown()`.
It must exist before `new_closeup.gd` runs.

## Items list

`art-source/work/items/<part>.json`, read by `new_item.gd`, which writes
`content/items/<id>/<id>.tres` (an `ItemDef`).

| Field | Meaning |
|---|---|
| `id` | The item id. `adv-art icons` wrote its icon to `content/items/<id>/icon.png`. |
| `name` | The name shown in the inventory |
| `icon` | `res://content/items/<id>/icon.png` |
| `look_file`, `look_cue` | The dialogue file (under `content/dialogue/`) and cue of its Look line |
| `combinations` | Other item id → the item the two make. Write each pair both ways. |

## `content/chapters.json`

Each part lists what it owns: `id`, `title`, `start` (one of its rooms),
`rooms`, `closeups`, `characters`, `dialogue`, `cutscenes`, plus `flags`,
`items` and `memories` (what a player holds on reaching its start, for QA
and tests that start mid-game) and `web` (`true` to ship it in the browser
build). The export leaves a part's rooms, close-ups, characters, dialogue and
cutscenes out of the web build unless `web` is true.
