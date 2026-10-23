# Bones and motions

## The fields of `npc.json`

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | snake_case; the folder `content/characters/<id>/` and the scene `<id>.tscn` |
| `speaker` | yes | The name its lines use in `.dialogue` files (`Keeper: …`) |
| `aliases` | no | Other speaker names for the same actor, for example the name the NPC remembers later in the story. Its subtitles follow whichever name a line uses |
| `painting` | yes | The accepted raw, with alpha (`art-source/raw/IMG-####/IMG-####-vN.png`) |
| `height` | yes | The figure's height on screen at scale 1, in pixels. The texture is trimmed and scaled to 1.5× this, headroom for close-up push-ins |
| `feet` | yes | Where the figure stands, in the painting's pixels. The actor's origin |
| `speech` | yes | Where subtitles hang, in the painting's pixels (above the head) |
| `subtitle_color` | no | RGB 0 to 1. Default a light grey |
| `grid` | no | Mesh grid spacing in texture pixels. Default 28. Smaller bends smoother and costs vertices |
| `keep_color` | no | `true` keeps the painting's colour; otherwise `adv-art npc` greys it |
| `bones` | yes | Below |
| `motions` | yes | Below |

`adv-art npc` writes `npc_spec.json` next to `npc.json`, with every point
moved into the shipped texture's pixels, the texture path and scale, and the
figure's outline (the click shape). `new_npc.gd` reads only `npc_spec.json`.

## Bones

Each bone is `{"name", "parent", "from", "to"}`, points in the painting's
pixels. `from` is the joint the bone turns around; `to` is where the part
ends.

1. **`Base`** first, `parent: ""`, from the feet straight up to the hips. It
   owns the legs and the hem. No motion names it.
2. **`Spine`**, parent `Base`, from the hips to the base of the neck, down the
   middle of the body.
3. **`Head`**, parent `Spine`, from the neck to the crown.
4. **Arms** that move: `ArmR`/`ArmL` from the shoulder to the elbow or the
   hand, parent `Spine`. A hand that gestures on its own gets `HandR`/`HandL`,
   parent the arm.
5. **A prop** the NPC holds gets its own bone, parented to the hand or arm
   that holds it, or to `Base` if it stands on the ground (a spade, a staff).

Every vertex of the mesh follows the bones nearest it, by inverse distance to
each bone's segment. Put each bone down the middle of its part, and leave
parts that never move to `Base` or `Spine`.

## Motions

Every NPC has `idle`, `talk_a` and `talk_b`. The actor alternates the two talk
motions, one per line.

**A loop:**

```json
"idle": {"loop": true, "bones": {"Spine": [0.8, 0.22, 0.0], "Head": [1.4, 0.13, 1.0]}}
```

`bones` maps a bone to `[degrees, hertz, phase]`: a sine sway around the rest
pose. Past's idles used 0.3 to 4 degrees at 0.1 to 0.5 Hz. Offset the phases
so the parts don't move as one.

**A talk loop** adds `voice`:

```json
"talk_a": {"loop": true, "bones": {"Head": [1.5, 0.2, 1.0]}, "voice": {"Head": 5.0, "ArmL": -12.0}}
```

`voice` maps a bone to the degrees it bends at full loudness. The loudness is
the playing line's envelope (`Voice.level()`), or a lively stand-in when the
line has no audio yet. Past used 4 to 16 degrees.

**A one-shot:**

```json
"lean": {"loop": false, "length": 2.4, "keys": {"Spine": [[0.0, 0.0], [0.7, 6.0], [1.6, 6.0], [2.4, 0.0]]}}
```

`keys` maps a bone to `[seconds, degrees]` pairs, eased between. Start and end
every bone at 0 so the NPC returns to its idle. `await actor.play(&"lean")`
returns when it ends.

## Budget

Past's NPCs: 4 to 7 bones, about 285 vertices, a texture around 363×651, under
1 MiB of video memory each, and about 15 minutes of tracing once the tools
existed.
