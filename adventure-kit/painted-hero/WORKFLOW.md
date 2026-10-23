# painted-hero workflow

Run everything from the game's root (a project made by
[../new-adventure](../new-adventure/SKILL.md)). Paths below use the hero's
work folder:

```sh
W=art-source/work/characters/hero
B=/Applications/Blender.app/Contents/MacOS/Blender      # Blender 4.5 LTS
```

## Day one: the stand-in

A new game already has a hero: a stand-in drawn in code, so rooms, puzzles
and QA work before any painting.

```sh
tools/adv-art placeholder-hero --out $W        # renders/ at 12 fps, renders-walk/ at 8 fps
tools/adv-art pack --renders $W/renders --renders $W/renders-walk --out-dir content/characters/hero/sprites \
    --manifest $W/hero_sprites.json --res-prefix res://content/characters/hero/sprites --name hero --shaded
```

Then the import and `import_sprites.gd` lines of step 6. The stand-in's
folders are in the rig's anchors.json format, with every animation the
painted hero will have, so nothing else in the game changes when the painted
set replaces it.

## 0. The base mesh (once per machine or game)

The rig's body is the realistic male from Blender Studio's **Human Base
Meshes** bundle, CC0 (no attribution needed). Past used v1.4.1.

1. Download the bundle from <https://www.blender.org/download/demo-files/>
   (Past's copy came from
   `https://mirror.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip`)
   and unzip it into a scratch folder outside the project.
2. Copy out only the body and its two eye markers (about 12.6 MB):

   ```sh
   $B -b --disable-autoexec -P <this skill>/scripts/extract_base_mesh.py -- \
       <unzipped bundle folder> art-source/vendor/human-base-meshes/body_male_realistic.blend
   ```

   It finds the .blend that holds `GEO-body_male_realistic`,
   `...eye.L` and `...eye.R` and saves them with their multires sculpt.
3. Add `art-source/vendor/human-base-meshes/README.md` with the bundle's
   name, version, download URL, date and "CC0".
4. `export HERO_BASE_MESH=art-source/vendor/human-base-meshes/body_male_realistic.blend`

Always run Blender with `--disable-autoexec` on downloaded files.

## 1. The rig, in the game

```sh
mkdir -p tools/blender && cp <this skill>/scripts/pose_rig.py tools/blender/pose_rig.py
cp <this skill>/templates/hero_rig.json $W/hero_rig.json       # optional: height, frame, stance
```

The game owns its copy: new actions and pose fixes go into
`tools/blender/pose_rig.py`. `--config` keys are listed in its docstring;
leave `frame_size` and `character_px` alone once frames exist, because
`pack` refuses folders that disagree.

Quick look, one frame per animation and direction (about a minute):

```sh
$B -b --disable-autoexec -P tools/blender/pose_rig.py -- --out $W/preview --preview [--config $W/hero_rig.json]
tools/adv-art sheet --out build/review/rig-preview.png --columns 6 --tile 224x336 $W/preview/*/*_000.png
```

## 2. The model sheet

One request through [../art-requests](../art-requests/SKILL.md). Copy
`art-source/requests/_TEMPLATE.md` to `IMG-####-hero-model-sheet.md`, use
the model-sheet block and prompt in
[references/requests.md](references/requests.md), with a room's accepted
style key as the reference, then:

```sh
bun tools/images/run.ts IMG-####
```

Review the variants against the acceptance criteria, accept one, record why.
Show the operator the accepted sheet before step 3. If none passes, `status:
revise` with numbered notes; the next round continues the numbering.

## 3. Renders

```sh
$B -b --disable-autoexec -P tools/blender/pose_rig.py -- --out $W/rig --fps 12             # every animation, r u d
$B -b --disable-autoexec -P tools/blender/pose_rig.py -- --out $W/rig-walk8 --anims walk --fps 8
```

Each prints a `HERO_RENDER {...}` summary. Each folder holds
`<anim>_<dir>/<anim>_<dir>_NNN.png` and `anchors.json`. `rig/` and
`rig-walk8/` are the pose rig's; `renders/` and `renders-walk/` beside them
are the stand-in's, so neither overwrites the other. Renders rebuild in
minutes, so keep them out of git; commit the rig and the specs.

## 4. Guides

```sh
cp <this skill>/templates/painted.json $W/painted.json
tools/adv-art painted --guides $W/painted.json         # -> $W/guides/sheets/<sheet>.png
```

The template has 12 sheets: per direction one walk sheet and three key-pose
sheets (`poses_a`: idle, talks, look-around, fidget_a; `poses_b`: use, give,
flare, fidget_b; `poses_c`: the pick-ups and the rest of fidget_b). Every
`raw` is `null` until a sheet is accepted. Look at each guide: eight
distinct, readable poses, nothing clipped at the cell's edge. Field
reference: [references/painted-json.md](references/painted-json.md).

## 5. Painting, sheet by sheet

Order: `walk_r` first and accept it, because it becomes the third reference
of every later sheet. Then `walk_d`, `walk_u`, then the pose sheets.

1. Write the request from the walk-sheet or key-sheet block in
   [references/requests.md](references/requests.md): references `guide`,
   model sheet, accepted side walk (not for `walk_r` itself); `n: 3`;
   `background: transparent`; `model: codex/gpt-6.1-sol`.
2. `bun tools/images/run.ts IMG-####`
3. Review against the per-sheet checklist in [SKILL.md](SKILL.md). Accept,
   or revise with notes ("the coat is short", "frame 6 copies frame 2").
4. Set the sheet's `raw` in `$W/painted.json` to
   `art-source/raw/IMG-####/IMG-####-vN.png`.
5. Build (step 6) and read the report before requesting the next sheet in
   the same direction.

Sol can generate the next sheet while the last one is built.

## 6. Frames, sheets and the game resource

All of it, in one command:

```sh
tools/build/build_hero.sh
```

What it runs, in order, if you need one step:

```sh
# frames: cut, register, paint out the eyes; anchors.json in the render folders' format
tools/adv-art painted $W/painted.json > $W/painted-report.json

# sheets + manifest: trimmed, grey + alpha, marked painted
tools/adv-art pack --renders $W/painted --out-dir content/characters/hero/sprites \
    --manifest $W/hero_sprites.json --res-prefix res://content/characters/hero/sprites \
    --name hero --shaded --style painted

# lossless import: VRAM compression blocks up painted ink
tools/godot.sh --headless --import
sed -i '' 's/^compress\/mode=.*/compress\/mode=0/' content/characters/hero/sprites/*.png.import
tools/godot.sh --headless --import

# the CharacterSprites resource the game loads
tools/godot.sh --headless --script res://addons/adv_tools/import_sprites.gd -- \
    --manifest=$W/hero_sprites.json --out=res://content/characters/hero/hero_sprites.tres
```

`painted` skips an animation whose sheets are not all accepted yet, so a
partial set still builds while sheets come in. Missing `_l` frames mirror
`_r`, and a missing direction falls back to the nearest one the set has.
`pack` prints each animation's fps and frame count.

While sheets come in, the stand-in can fill the gaps: list its folders first
and the painted one last, and each painted animation replaces the stand-in's
of the same name (a later `--renders` folder wins). `pack` needs every
folder at the same `frame_size` and `character_px`; the stand-in frames are
then drawn as painted too, which is fine for a few days.

```sh
tools/adv-art pack --renders $W/renders --renders $W/renders-walk --renders $W/painted \
    --out-dir content/characters/hero/sprites --manifest $W/hero_sprites.json \
    --res-prefix res://content/characters/hero/sprites --name hero --shaded --style painted
```

## 7. The hero scene

`content/characters/hero/hero.tscn` (made by `scaffold_core.gd`): an `Actor`
with `depth_speed = 0.6`, `step_with_frames = true`, `talk_animations =
[talk_a, talk_b]`, a `Body` child with `HeroBody` and `sprites =
hero_sprites.tres`, and an `IdleFidgets` child. Never hand-edit the `.tscn`.

## 8. Checks

```sh
tools/test.sh
tools/godot.sh -- --qa=hero_anims --qa-out="$PWD/build/qa/hero"
```

`hero_anims` plays every action in every direction, shoots each at its
middle, and fails if an animation is missing or never passes its middle.
Then the reel for the operator:

```sh
tools/godot.sh --write-movie "$PWD/build/qa/hero/reel.avi" --fixed-fps 30 -- --qa=hero_anims --force-draw
```

(Put a temporary `override.cfg` with a 1920x1080 window in the project root
while recording, and delete it after: see
[../ship-check](../ship-check/SKILL.md).) Walk the hero across a room with
foreground occluders and a far-to-near scale zone, and watch the planted
foot. Evidence goes in `docs/qa/<plan>/`.

## Adding an action

1. In `tools/blender/pose_rig.py`: a function that keys the motion through
   `Poser.pose` and `Poser.lift`, an `ANIMATIONS` entry (function, length in
   24 fps frames, loop) and any `EVENTS`.
2. Render only it, into its own folder (rendering into `$W/rig` would
   rewrite that folder's `anchors.json` with only the new action):
   `--anims <name> --out $W/rig-<name> --fps 12`. Check the frames on a
   contact sheet.
3. Pick 2 or 3 key frames: the extremes where the motion holds. Add them to
   a sheet (any sheet with free cells in that direction, or a new one) as
   cells `["<name>_<d>_<frame>", "$W/rig-<name>", "<name>_<d>", <frame>]`
   (with `$W` written out), and an animation entry
   `{"keys": ["idle_<d>", ...], "from": ["<the rig-<name> folder>", "<name>_<d>"]}`.
4. `tools/adv-art painted --guides`, request, accept, `build_hero.sh`.
5. Add the name to the game's animation list and to the `hero_anims` QA run.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| A painted frame floats or sinks | The cell's figure has stray paint below the feet, or Sol moved it far. Read its `shift` in the report; revise the sheet if it is far off. |
| Eyes missing in a profile or front frame | Sol painted them faint or merged them with the rim. Check `eyes` in the report; a bowed or turned head with none is fine. |
| Front or back frames look heavy | `squeeze` not 0.8 or `thin` 0 on that sheet; fix the spec, rewrite the guide, request again. |
| An action jumps between two drawings | Its keys are too far apart in pose; add a middle key on a sheet. |
| The walk slides | The walk's `ground_px_per_second` didn't reach the manifest (the walk's `from` must be the 8 fps render, `rig-walk8`), or the actor lacks `step_with_frames`. |
| `pack` refuses a folder | Its `frame_size` or `character_px` differs from the others. Re-render with the same config. |
