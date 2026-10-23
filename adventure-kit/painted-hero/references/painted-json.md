# painted.json

The spec `tools/adv-art painted` reads, one per character, in
`art-source/work/characters/<id>/painted.json`. Every path is relative to the
game's root. [../templates/painted.json](../templates/painted.json) is a full
hero set: 12 sheets, 36 animations.

## Top level

| Key | Type | Meaning |
|---|---|---|
| `out` | path | Where the painted frames go: `cells/<cell>.png`, one folder per animation, and `anchors.json` in the render folders' format |
| `guides` | path | Where `--guides` writes `<sheet>.png` |
| `frame_size` | [w, h] | The render frame in pixels. Must match the rig's renders (pose_rig default 448 x 672) |
| `character_px` | int | How tall the character stands in the frame at scale 1 (default 480). Copied into the output |
| `sheets` | object | Sheet name -> sheet |
| `animations` | object | Animation name (`<anim>_<dir>`) -> animation |

## A sheet

One 4 x 2 guide, and the painting of it once accepted.

| Key | Type | Meaning |
|---|---|---|
| `view` | `r`, `d` or `u` | The direction drawn. Sets which eyes `painted` looks for: one in profile (`r`), two from the front (`d`), none from the back (`u`) |
| `raw` | path or `null` | The accepted painting, `art-source/raw/IMG-####/IMG-####-vN.png`. `null` (or missing) until then: `--guides` still writes the guide, the build skips the sheet |
| `cells` | list | Up to 8 `[cell name, renders folder, render animation, frame index]`, in reading order (top row left to right, then the bottom row). The cell name is how animations refer to the drawing: `walk_r_3`, `use_d_7`, `idle_u` |
| `crop` | [x, y, w, h] | Optional. The part of the render frame each cell shows. Default: the union of the cells' silhouettes plus 24 px, grown to the cell's 3:4 shape, with the extra room above (raised hands, hair). Walk sheets use a fixed crop (`[34, 125, 380, 520]` at 448 x 672) so every frame of the cycle is at one scale |
| `thin` | int | Pixels the mannequin is eroded in the guide. 0 for the side walk, 5 for everything else in Past |
| `squeeze` | float | Optional. Narrows the guide about the crop's centre: 0.8 is 80% as wide. Use 0.8 for front and back views. The squeeze carries into the frames, their anchors and the leg registration |

## An animation

Either a list of cells played in order (walks, single drawings), or keys held
on the rig's timing (limited animation).

| Key | Type | Meaning |
|---|---|---|
| `from` | [renders folder, render animation] | The rig animation this one takes its frame count, fps, loop, events and ground speed from |
| `cells` | list of cell names | Played in this order, one per frame. Walks: the 8 walk cells. A still: one cell |
| `keys` | list of cell names | Instead of `cells`: each frame of `from` shows the key whose head and hands are nearest that frame's pose. Put the idle drawing first, so the start and end of an action rest on it |
| `fps` | number | Optional. Overrides `from`'s rate (walks: 8) |
| `loop` | bool | Optional. Overrides `from`'s loop flag (the idle still: `true`) |

An animation is skipped while any cell it names comes from a sheet with no
`raw`.

## Output

`out/anchors.json` has `frame_size`, `character_px`, `fps` and per animation
`fps`, `frames`, `loop`, `anchors` (one dict per frame), `events` and, for
walks, `ground_px_per_second`. Each frame's anchors are the rig's, squeezed
if the sheet was, with `eye_l`, `eye_r` and `eyes_visible` replaced by where
the painted eyes were found.

`painted-report.json` (the command's stdout): per cell, its sheet, the
registration `shift` [dx, dy] and the number of `eyes` found; per animation,
the frame-by-frame key sequence (for example `idle 5 5 11 11 idle`).

## The rig's renders, as `painted` and `pack` read them

`<folder>/anchors.json`:

```json
{"frame_size": [448, 672], "character_px": 480, "fps": 12.0,
 "animations": {"walk_r": {"fps": 8.0, "frames": ["walk_r_000.png", "..."], "loop": true,
   "anchors": [{"head": [x, y], "eye_l": [x, y], "eye_r": [x, y], "eyes_visible": [false, true],
                "shoulder_l": [x, y], "shoulder_r": [x, y], "back": [x, y],
                "hand_l": [x, y], "hand_r": [x, y], "feet": [x, y]}, "..."],
   "events": [{"frame": 0, "name": "step"}, {"frame": 4, "name": "step"}],
   "ground_px_per_second": 356.3}}}
```

Frames are `<folder>/<anim>_<dir>/<anim>_<dir>_NNN.png`, RGBA, at
`frame_size`. Any rig that writes this format can drive the pipeline.
