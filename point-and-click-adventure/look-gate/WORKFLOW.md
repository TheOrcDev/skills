# look-gate workflow

From the repository root of a game made with
[new-adventure](../new-adventure/SKILL.md). `<skill>` is this skill's folder.

## 1. Brief and style bible

```sh
mkdir -p docs/reference art-source/style/prompts art-source/style/landmarks art-source/work/specs
# the operator's concepts go in docs/reference/, unedited
```

Fill [templates/style-bible.md](templates/style-bible.md) into
`docs/art-pipeline.md` §2 to §4. Ask the operator only what the concepts
don't show: one era or two, the hero's idea, the tone. Write the marker table
(section 1) last, from the rest.

## 2. Preambles

```sh
cp <skill>/templates/preambles/*.txt art-source/style/prompts/
# edit each file: replace every [[MARKER]] with the bible's fill
grep -n '\[\[' art-source/style/prompts/*.txt && echo "markers left" || echo "preambles ready"
```

- One-era game: delete `then.txt`.
- Keep the `{fields}` exactly as named: `tools/images/src/templates.ts` fills
  them from each spec and refuses a spec that leaves one out.

| Preamble | Fields |
|---|---|
| `now` | `setting`, `composition`, `ground`, `light` |
| `then` | `keep`, `place`, `when`, `restore` |
| `closeup` | `subject`, `detail`, `lettering` (end it with a space, or leave it empty) |
| `npc` | `character`, `face`, `pose` |
| `items` | `count`, `grid`, `items` |

## 3. A/B the engines

Write one `now` spec for the area's first room, twice: once with the default
model (Sol) and once with `"model": "openai/gpt-image-2.5-flare"` and
`"quality": "medium"`. With no style key yet, reference the operator's
concept from `docs/reference/`.

```sh
bun tools/images/check.ts                               # gateway credential and models
bun tools/images/new-request.ts art-source/work/specs/ab.json
bun tools/images/run.ts IMG-0001 --dry-run && bun tools/images/run.ts IMG-0001
bun tools/images/run.ts IMG-0002 --dry-run && bun tools/images/run.ts IMG-0002
tools/adv-art sheet --out build/review/ab.jpg --columns 3 \
  art-source/raw/IMG-0001/IMG-0001-v1.png:Sol-v1 art-source/raw/IMG-0001/IMG-0001-v2.png:Sol-v2 \
  art-source/raw/IMG-0001/IMG-0001-v3.png:Sol-v3 art-source/raw/IMG-0002/IMG-0002-v1.png:Flare-v1 \
  art-source/raw/IMG-0002/IMG-0002-v2.png:Flare-v2 art-source/raw/IMG-0002/IMG-0002-v3.png:Flare-v3
bun tools/images/budget.ts
```

Judge by the composition rules (open floor, horizon, exits, hotspots
separated, walk band values) and the style. Record the pick in both requests'
Review tables, and add a decision: the default engine and model for new
images, edits, NPCs and items, with the cost per image.

## 4. The style key and landmarks

The winning request becomes the style key (or run one more round on the
winning engine with notes). Set `operator-approval: required` and show the
operator before recording `**accepted: vN**`.

```sh
cp art-source/raw/IMG-0001/IMG-0001-v2.png art-source/style/<area>-style-key.png
# landmarks: crop with any tool into art-source/style/landmarks/<name>.png; note the source IMG in the bible
```

Two-era game: write the key's then-spec (`kind: "then"`, the accepted raw as
the reference), run it, and measure:

```sh
tools/adv-art align --fixed art-source/raw/IMG-0001/IMG-0001-v2.png \
  --moving art-source/raw/IMG-0003/IMG-0003-v1.png --report build/review/IMG-0003-v1-align.json
```

Exit 0 means p90 ≤ 3 px. Above it, a revise round with the drift named in the
notes; after two, STOP.

## 5. Measure the walk band

Trace the walk area roughly on a 1920×1080 grid, then grade:

```sh
tools/adv-art grid --in art-source/style/<area>-style-key.png --out build/review/key-grid.png
tools/adv-art grade --in art-source/style/<area>-style-key.png --out build/review/key-1080.png \
  --size 1920x1080 --walk-polygon '[[100,760],[1820,760],[1900,1060],[20,1060]]'
```

`walk_area_luminance` is the floor; `behind_figure_luminance` is the band
where the hero's head and shoulders are seen. For a dark hero, both should be
clearly mid-to-light; confirm with a screenshot in step 7.

## 6. The hero model sheet

A `raw` spec from the hero sheet example in
[art-requests/templates/specs.json](../art-requests/templates/specs.json),
with the design written from the bible's section 3 and the style key as the
reference. `operator-approval: required`.

- Show every round to the operator with your recommendation.
- Change one thing per round, or present one whole coherent redesign.
- Must not have: an alien look (bulbous head, slanted eyes, a naked body),
  realistic muscle anatomy.
- Composite the accepted sheet over the style key at the hero's scale to
  check it belongs in the room.
- Copy it to `art-source/style/hero-model-sheet.png` and continue in
  [painted-hero](../painted-hero/SKILL.md).

## 7. One room in the engine

Build the style key's room with [paint-room](../paint-room/SKILL.md)
(room.json, `adv-art room`, `new_room.gd`, hotspots, effects, both eras).
Then:

```sh
tools/test.sh
tools/godot.sh -- --qa=rooms --rooms=<room_id> --qa-out="$PWD/docs/qa/<plan>/rooms"   # quick look; --qa-out is absolute
tools/build/export.sh macos
build/macos/<Game>.app/Contents/MacOS/<Game> --resolution 1920x1080 -- --qa=perf --qa-out="$PWD/docs/qa/<plan>/perf"
tools/build/export.sh web && bun tools/build/serve.ts &
bun tools/build/browser-qa.ts perf 1920x1080 2
```

Details of the builds and the browser checks are in
[ship-check](../ship-check/SKILL.md).

## 8. Record and gate

Write `docs/qa/<plan>/README.md`:

| Measure | Desktop | Browser |
|---|---|---|
| Frame time at 1080p (mean, p95, worst) | | |
| Video memory | | |
| Download (pack, wasm) | — | |

| Asset | Requests | Rounds | Accepted | Cost | Hours |
|---|---|---|---|---|---|
| Style key | | | | | |
| Then-edit | | | | | |
| Hero model sheet | | | | | |

Add screenshots of both eras and the hero at the near and far walk lines and
the darkest spot. Show the operator; record the sign-off as a decision and in
the bible's section 9.
