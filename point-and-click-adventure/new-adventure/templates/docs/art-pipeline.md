# {{GAME_NAME}}: Art Pipeline

Status: draft, {{DATE}}. Inherited from the point-and-click-adventure kit. The look-gate plan
proves it on one area before any volume production starts. Numbers marked
*calibrate* are set by that plan.

## 1. Who does what

| Role | Does |
|---|---|
| **Image tool** (`tools/images`, run by Claude) | Generates every image from a request file, through **GPT-6.1 Sol** in Codex (`codex/gpt-6.1-sol`: 1672×941 landscape whatever the size asks, no masks) or OpenAI's GPT Image models through the Vercel AI Gateway (masks, exact sizes, fallbacks). Backgrounds, then-edits, outpaint zoom-outs, clean plates, character sheets, UI art, journal illustrations and title cards. It writes receipts and enforces the plan's image budget. |
| **Claude** | Writes the requests, runs the tool and reviews what comes back. Does all processing (alignment, depth, layers, grading, upscaling), the hero's rig and painted frames, NPC skinning, effects, Godot integration and QA. |
| **Operator** | Reviews style keys, the hero's model sheet and each area's look, and can overrule any pick. |

The request, delivery and review protocol is in `../AGENTS.md`. The template is
`../art-source/requests/_TEMPLATE.md`.

## 2. Style bible

### Present ("now")

- {{MEDIUM: for example a monochrome matte painting with an ink-wash texture}}
- {{DEPTH: how distance reads, for example fog that is pale far and dark near}}
- {{FRAMING: what frames the foreground}}
- {{ARCHITECTURE and setting vocabulary}}
- {{CONDITION: ruin, wear, season, weather}}
- {{LIGHT: where it comes from and how it separates silhouettes}}

### Past or second state ("then")

{{Delete if the game has no second state.}}

- The **same composition and camera** as the present image, made as an edit of
  it and never generated from scratch.
- {{WHAT_CHANGES: colour, restoration, life}}
- The key light comes from the same direction as in the present image, so shapes
  still match during the transition.

### The hero

- {{SILHOUETTE: the shape, clothes and features that read at small size}}
- {{LINE_AND_SHADING: for example a bold brush outline, a thin rim, sparse
  hatching}}
- A light rim on the outline separates the hero from dark areas.

### Landmarks

Recurring landmarks keep the geography readable: {{LANDMARKS}}. Once a
landmark is approved, Claude crops it into `art-source/style/landmarks/`, and
later requests reference that crop.

### Always

- Backgrounds contain no characters. The hero and the NPCs are separate layers.
- No text, signatures, frames or watermarks.
- {{GRADE_RULE: for example, the present is delivered in greyscale and any tint
  is applied in the engine, so the transition shader controls where colour
  returns}}

## 3. Composition rules for playable rooms

These rules go into every room request (the `now` preamble):

1. The camera is at eye level or slightly above, with the horizon at 40–55% of
   the frame height.
2. A clear walkable floor fills the lower 30–40% of the frame, with exits at the
   left and right edges or as visible doors.
3. **The walkable band contrasts with the hero.** A dark hero walks against
   mid-to-light fog, so the darkest values belong in the foreground framing and
   the top corners, never behind the hero's path. `adv-art grade` measures it.
4. Three to six distinct interactive objects, each separated from its
   background by rim light or fog.
5. Foreground occluders such as columns and railings let the hero walk behind
   them without hiding any hotspot.

## 4. Technical targets

| Item | Target |
|---|---|
| Viewport | 1920×1080, letterboxed to 16:9 |
| Room background | 1920×1080 per screen. A scrolling room is up to 3 screens wide. |
| Sol images | 1672×941, upscaled 1.15× with Lanczos to 1920×1080 by `adv-art room` |
| Gateway images | Sizes are multiples of 16, aspect between 1:3 and 3:1. Rooms 2560×1440 then downsampled; vista rings 3:1 (for example 3840×1280). Flare for new images, Sunburst for edits. |
| Quality | `medium` while exploring, `high` for finals, `max` only for hero images |
| Upscaling | Only where the camera pushes in beyond the generated size |
| The hero's height | About 480 px at the nearest walk line, roughly 44% of the screen. *Calibrate.* |
| Animation | Walk {{8}} frames per direction at {{8}} fps; other actions 2–3 key drawings on the rig's timing |
| Directions | Right, up and down; left mirrors right. Diagonals only if worth their memory. |
| The hero's frames | Trimmed, packed, imported lossless, 128 MiB of video memory at most |
| Atlases | At most 4096×4096, loaded per room and per character |
| Source format | Lossless PNG in `art-source/` |

Draw everything at its largest on-screen size and only scale down.

## 5. Pipelines

### A. Rooms (now and then)

1. **Request:** the room's purpose, composition notes (floor zone, exits,
   hotspots, occluders), the style key and landmark crops as references, from
   the `now` preamble. The first room of every area is its style key.
2. **Generate** (`bun tools/images/run.ts IMG-xxxx`): 3 variants with a
   receipt.
3. **Pick:** Claude accepts its recommended variant and records why.
4. **Then version:** a request that edits the accepted now image ("same
   composition, camera and perspective; restore …"), from the `then` preamble.
5. **Process** with `tools/adv-art`, into `art-source/work/rooms/<room>/`:
   - `align` the then image to the now image. A p90 residual above 3 px means a
     revision; after two Sol misses, the gateway's Sunburst;
   - trace `room.json` on `grid`, check it on `overlay`;
   - `room` grades the now image, aligns the then image, makes depth, cuts
     occluders in both eras, cuts props and clean plates, and writes
     `room_spec.json`.
6. **Assemble:** `new_room.gd` with the spec, then the room's script: hotspot
   lines, exits, puzzle logic.
7. **QA:** `test_rooms_all.gd` and `--qa=rooms --rooms=<id>`.

### B. Vistas and discovery reveals

- **Nested zoom stack:** three 3:1 rings through the gateway. Ring 0 from Flare;
  rings 1 and 2 as Sunburst 2× repaints of the centre of the ring outside.
  `adv-art reveal --sources` cuts the crops for the next ring's request, and the
  build writes the rings and `reveal_spec.json` for `new_reveal.gd`.
- **Past vistas** are edits of the present vistas, or a room's then image.

### C. The hero: painted over a rig's poses

1. **Model sheet** (Sol): front, side, back, three-quarter views, on a plain
   background. Clothes give the silhouette.
2. **Pose rig** (Blender, bpy, keyframed by Claude): renders every animation
   and direction with anchors, step events and ground speed.
3. **Guides:** `adv-art painted --guides` lays frames 4 × 2 on a 1536 × 1024
   sheet, thinned and tone-lifted; front and back squeezed to 80% width.
4. **Painting:** Sol repaints each sheet, with the guide, the model sheet and
   the accepted side walk as references.
5. **Frames:** `adv-art painted` cuts each cell, maps it back into the render
   frame, registers the legs on the guide's soles and paints out painted eyes.
6. **Build:** `tools/build/build_hero.sh` packs the sheets and imports them
   lossless.

### D. NPCs: skinned paintings

Sol paints each NPC once on transparent. `adv-art npc` trims it to 1.5× its
on-screen height; `new_npc.gd` meshes it inside its alpha and skins it to a
`Skeleton2D` of 5–8 bones. The base bone never moves, so the feet stay planted.
NPCs are designed to read by outline: hats, cloaks, tools, posture.

### E. Living-painting effects (procedural)

- **Fog:** tileable noise scrolling at different speeds per depth band, with
  density from the depth map.
- **Light shafts:** additive gradients with a slow flicker.
- **Particles** (`CPUParticles2D`): ash, rain, embers, dust, birds.
- **Water:** reflection and ripple distortion.
- **Cloth:** a vertex wave on banners cut into their own layer.
- **Transition:** a noise-masked radial dissolve between the aligned era layers.

### F. UI art and fonts

- Image tool, with transparent backgrounds where needed: verb coin glyphs,
  cursors, inventory and journal art, title cards, the start screen and logo.
- **Fonts:** open-licensed (OFL) only. A display face for titles and a very
  readable face for subtitles, tested at 1080p.

### G. Close-ups and items

- **Close-ups:** Sol paints the detail from the `closeup` preamble;
  `adv-art closeup` builds `closeup_spec.json` for `new_closeup.gd`.
- **Items:** one Sol sheet per part from the `items` preamble; `adv-art icons`
  cuts it in reading order into `content/items/<name>/icon.png`;
  `new_item.gd` makes the items.

## 6. Folder layout and naming

```
art-source/            # never imported by Godot (.gdignore)
  requests/            # one file per image request; Claude writes, the tool fills delivery
  requests/INDEX.md    # rebuilt by bun tools/images/index.ts
  raw/IMG-0001/        # tool output, immutable: IMG-0001-v1.png …, receipt.json
  raw/ledger.json      # every generation call with its cost, per plan
  work/                # Claude: rooms/<id>/room.json, characters/<id>/, closeups/, reveal/
  style/               # style keys, landmark crops, prompts/ (now, then, closeup, npc, items)
docs/reference/        # the operator's original concepts
```

- Requests use sequential IDs, `IMG-0001-<kebab-slug>.md`.
- Rooms use `snake_case` ids.
- Era suffixes are `_now` and `_then`. Layer suffixes are `_bg`, `_mid`,
  `_fg`, `_occ` and `_depth`.
- Every raw keeps its receipt with the prompt, model, size and date. Receipts
  back any AI-content disclosure a store requires.
- Decide on Git LFS before volume art: a Sol raw is about 3.5 MB, and 50 rooms
  came to about 1.7 GB in Past.

## 7. Art tools

| Tool | Job |
|---|---|
| `tools/images` | Runs a request: text-to-image, or an edit with references and a mask. Writes the raws, `receipt.json` and the ledger. Enforces the plan's budget. `new-request.ts` writes requests from short specs and the shared prompts; `index.ts` rebuilds the index; `check.ts` checks credentials. |
| `adv-art align` | SIFT + RANSAC registration with a residual report |
| `adv-art grade` | Resize, optionally make monochrome, and measure the walk band |
| `adv-art mask`, `cut` | Polygon masks and RGBA cut-outs |
| `adv-art depth` | A depth map (`uv sync --extra depth`) |
| `adv-art grid`, `overlay` | A labelled grid for tracing; a room's traced data drawn on its image |
| `adv-art room` | A room's art and `room_spec.json` from `room.json` |
| `adv-art closeup`, `icons` | Close-ups and item icons |
| `adv-art npc` | An NPC painting and `npc_spec.json` from `npc.json` |
| `adv-art painted`, `pack` | The hero's painted frames and sprite sheets |
| `adv-art ring`, `reveal` | Reveal rings and `reveal_spec.json` |
| `adv-art sheet` | Contact sheets for review |

## 8. Quality gates

1. Each area's style key is accepted before more than three of its rooms are
   generated.
2. Then/now alignment has a p90 of at most 3 px.
3. The hero stays readable everywhere on the walkable area: the `grade` check
   passes and a screenshot at the darkest spot is reviewed.
4. Hotspots can be found with labels off.
5. No visible seams in layers or zoom stacks at 1080p or at maximum zoom.
6. Download size and performance stay inside `technical-plan.md` §10.
