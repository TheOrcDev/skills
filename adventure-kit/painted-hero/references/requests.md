# Request blocks for the hero

Three kinds of request, each a normal request file
(`art-source/requests/IMG-####-<slug>.md`, see
[../../art-requests](../../art-requests/SKILL.md)). Fill the placeholders
once and paste the same text into every request, so every sheet describes
the same character in the same words.

- `{DESIGN}`: who the hero is, in one paragraph: the silhouette (clothes,
  hair, props), the colours or values, the face (what it has and lacks), the
  build, the personality, and what it must never look like.
- `{MEDIUM}`: how it is drawn, matching the rooms (Past: "halfway between an
  inked graphic-novel comic and a hand-drawn animated film: a bold brush
  outline, a thin moonlight rim line and sparse hatching").
- `{VIEW}`: per direction. `r`: "He faces right in full profile, as the guide
  does, with his one visible eye." `d`: "He faces the viewer, seen from the
  front as in the guide." `u`: "He faces away from the viewer, seen from the
  back as in the guide."

## 1. Model sheet

```json
{
  "model": "codex/gpt-6.1-sol",
  "size": "2560x1440",
  "quality": "high",
  "n": 3,
  "background": "transparent",
  "references": ["<an accepted room image, for the palette>"],
  "mask": null
}
```

```text
A character model sheet for the hero of a point-and-click adventure game, drawn {MEDIUM}, in the palette of the attached painting, so he belongs in that world while reading clearly against it.

The character: {DESIGN}

The sheet shows four views of the same character side by side, evenly spaced, all exactly the same height, standing on one shared invisible baseline: 1) full profile facing right, 2) front, facing the viewer, 3) back, facing away, 4) three-quarter view facing right. A relaxed neutral standing pose in every view, arms hanging a little away from the body so the hands are clearly visible, feet slightly apart. Each figure shown whole from head to toes, filling most of the image height.

On a fully transparent background, with no ground, cast shadow or scenery. No text, labels, letters or numbers. No watermark, signature or border.
```

Acceptance: reads as an appealing hero at thumbnail size; fits the rooms'
palette; the same design in all four views; hands clear of the body in the
front and back views.

## 2. Walk sheet

References: the guide, the model sheet, and (for `walk_d` and `walk_u`) the
accepted side walk.

```json
{
  "model": "codex/gpt-6.1-sol",
  "size": "2560x1440",
  "quality": "high",
  "n": 3,
  "background": "transparent",
  "references": [
    "art-source/work/characters/hero/guides/sheets/walk_d.png",
    "art-source/raw/IMG-####/IMG-####-vN.png",
    "art-source/raw/IMG-####/IMG-####-vN.png"
  ],
  "mask": null
}
```

```text
Edit the first image. It is an animation pose guide: 8 frames of a walk cycle, in 2 rows of 4, read left to right, top row first, each grey mannequin showing one pose. Repaint it as a finished 2D game animation sprite sheet of the character from the model sheet (the second image), drawn {MEDIUM}, exactly as in the third image, a finished sheet of him, keeping the layout and the motion exactly as in the guide: the same 8 frames in the same order and the same cells, with the same pose of the legs, feet, arms, hands, body and head in every frame. {VIEW} Copy only the poses from the guide, never the mannequin's build: the character's own proportions are as in the model sheet. Draw him identically in all 8 frames, as a professional animator would, so they play back as one smooth walk. Only the motion changes: his legs and arms move exactly as the guide shows, and his clothes and hair follow the stride (<how the coat, hem, hair or props swing>).

Every figure is whole from head to feet and stays inside its own cell, at the same place and size as its mannequin, with clear empty space between neighbouring figures so none touch. Replace the grey background with full transparency: a fully transparent background, with no ground, cast shadow, smoke or scenery. No text, numbers, labels, grid lines or borders.
```

For `walk_r`, the first sheet, drop "exactly as in the third image, a
finished sheet of him" and the third reference.

Acceptance: each frame's pose matches its guide frame; the design is the same
in all 8 frames and matches the side walk; the cycle loops; nothing touches.

## 3. Key-pose sheet

```text
Edit the first image. It is a pose guide: 8 separate poses in 2 rows of 4, each grey mannequin showing one key drawing of a 2D game character's actions (<list the sheet's actions, e.g. standing still, two talking gestures, a two-handed explaining gesture, looking around over each shoulder and a thoughtful head tilt>). Repaint it as a finished sheet of key drawings of the character from the model sheet (the second image), drawn {MEDIUM}, exactly as in the third image, a finished sheet of him, keeping the layout exactly as in the guide: the same 8 poses in the same cells, each with the same pose of the legs, feet, arms, hands, body and head as its mannequin, at the same place and size. {VIEW} Copy only the poses from the guide, never the mannequin's build. Draw him identically in all 8 poses, as a professional animator would draw the keys of one character, so that they can be played in sequence. His clothes and hair follow each pose naturally: <how they hang, fold and drape when he bends, reaches or crouches>.

Every figure is whole from head to feet and stays inside its own cell, at the same place and size as its mannequin, with clear empty space between neighbouring figures so none touch. Replace the grey background with full transparency: a fully transparent background, with no ground, cast shadow, smoke or scenery. No text, numbers, labels, grid lines or borders.
```

The generation block is the walk sheet's, with the key sheet's guide first.

Acceptance: each pose matches its guide; the design matches the side walk;
nothing touches.

## Writing the Must not have

Name the failure seen last round, in the request's Must not have and in the
next round's Review notes: "the mannequin's heavy build", "a short coat",
"frames touching", "text or grid lines", "an alien look: bulbous head or
slanted eyes".
