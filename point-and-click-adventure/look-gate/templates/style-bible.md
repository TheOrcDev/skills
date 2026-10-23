# <Game> — Style bible

Status: draft <YYYY-MM-DD>. Signed by the operator at the look gate
(decision #<N>). This is `docs/art-pipeline.md` §2 to §4. Every image request
follows it; the preambles in `art-source/style/prompts/` are written from it.

Reference images: `docs/reference/` (the operator's concepts, never edited).

## 1. The style in one line

> <One sentence a model can follow. Example: "soft gouache storybook painting
> with visible brush texture, muted sea colours and warm lamplight".>

| Marker | Fill | Used by |
|---|---|---|
| `[[STYLE]]` | <the style phrase above, without articles> | now, closeup, npc, items |
| `[[GENRE]]` | <two or three words: "cosy seaside", "dark gothic"> | now, npc, items |
| `[[ATMOSPHERE]]` | <what sits behind the walk band: "drifting sea mist", "soft haze"> | now |
| `[[HERO_SILHOUETTE]]` | <how the hero reads: "a small black figure", "a figure in a red coat"> | now |
| `[[THEN_LOOK]]` | <the past era's look: "in full rich warm colour, as a painterly matte painting">; delete the then preamble if the game has one era | then |
| `[[NPC_LOOK]]` | <a sentence: "They are a solid figure in muted mid tones, never as dark as the hero"> | npc |

## 2. Eras

If places have two states (now and then), describe both. Skip this section
for a one-era game.

### Now (the present)

- Palette and values: <…>
- Texture: <…>
- Depth: <how near, mid and far separate: fog, haze, value steps>
- Framing: <what silhouettes frame the foreground>
- Light: <from where, what kind; rim light on silhouettes>
- Condition: <ruin, decay, neglect, or whatever the present is>

### Then (the past)

- The **same composition and camera** as the now image, made as an edit of
  it and never generated from scratch.
- Palette and light: <…>. The key light comes from the same direction as in
  the now image, so shapes still match during the transition.
- What comes back: <people's things, colour, life, light>.

If the eras differ by colour, the colourless era is delivered greyscale and
any tint is applied in the engine, so shaders control exactly where colour
returns.

## 3. The hero

- Shape: <the silhouette in one sentence; clothes give it>.
- Value: <the hero's darkest and lightest values, and where they must read>.
- Line and rendering: <outline, rim, hatching or flat colour>.
- Scale: <about 480 px tall at the nearest walk line, roughly 44% of the
  1080 px screen; the hero's scale against the architecture is part of the
  mood>.
- Model sheet: IMG-<####> v<N> (four views, one baseline).

## 4. NPCs

- How they differ from the hero: <value, colour, outline>.
- Faces: <hidden, turned away or masked, so nobody needs lip sync; or
  explain how mouths will be animated>.
- Each reads by outline: hat, hood, tool, posture.

## 5. Landmarks

Recurring world landmarks keep the geography readable. Once a landmark is
accepted, crop it into `art-source/style/landmarks/<name>.png`, and later
requests that show it reference the crop.

| Landmark | Crop | From |
|---|---|---|
| <lighthouse> | `art-source/style/landmarks/lighthouse.png` | IMG-<####> v<N> |

## 6. Composition rules for playable rooms

These go into every room request.

1. The camera is at eye level or slightly above, with the horizon at 40 to
   55% of the frame height.
2. A clear walkable floor fills the lower 30 to 40% of the frame, with exits
   at the left and right edges or as visible doors.
3. The walkable band sits against values the hero reads on: a dark hero
   needs mid-to-light values behind the path, so the darkest values belong in
   the foreground framing and the top corners, never behind the walk.
   `adv-art grade --walk-polygon` measures it.
4. Three to six distinct interactive objects, each separated from its
   background by rim light, haze or value.
5. Foreground occluders such as columns and railings let the hero walk behind
   them without hiding any hotspot.

## 7. Always

- Backgrounds contain no characters. The hero and the NPCs are separate
  layers.
- No text, signatures, frames or watermarks, except lettering a close-up
  needs, asked for in its `{lettering}` field.
- Draw everything at its largest on-screen size and only scale down.

## 8. Technical targets

| Item | Target |
|---|---|
| Viewport | 1920×1080, letterboxed to 16:9 |
| Room background | 1920×1080 per screen. Sol rooms upscale 1.15× from 1672×941 |
| Then/now alignment | p90 ≤ 3 px after `adv-art align` |
| Vista rings | 3:1 through the gateway, for example 3840×1280 |
| NPC paintings | Portrait, transparent, trimmed to 1.5× on-screen height |
| Item icons | One sheet per part, cut in reading order |
| Source format | Lossless PNG in `art-source/`, never imported by Godot |

## 9. Sign-off

| Gate | Evidence | Operator |
|---|---|---|
| Style key | IMG-<####> v<N>, `art-source/style/<area>-style-key.png` | <date, words> |
| Hero model sheet | IMG-<####> v<N> | <date, words> |
| One room in the engine | `docs/qa/<plan>/` | <date, words> |
