---
name: look-gate
description: Sets a point-and-click game's look before any volume art. Writes the style bible and composition rules for playable rooms, fills the shared prompt preambles (now, then, close-up, NPC, items), A/Bs the image engines on one brief, makes and accepts an area's style key and landmark crops, runs the hero's model-sheet rounds, proves one room in the engine with the hero at scale and measures fps, video memory and cost, then gets the operator's sign-off. Use when starting a game's art, setting or changing the art style, making a new area's style key, designing the hero's look, writing or fixing the prompt preambles, or when the user says "prove the look", "first light", "style key", "model sheet" or "look gate".
---

# look-gate

Fifty rooms that don't match are worse than five that do. This skill decides
the look once, writes it down where every later request reads it, and proves
it in the real engine before the volume starts. Past did it in plan 002: one
room, both eras, the hero walking, the flashback and a reveal, for $0.46 of
image spend, signed before the next 50 rooms.

Read [RULES.md](RULES.md) first. Commands are in [WORKFLOW.md](WORKFLOW.md).
Every image goes through [art-requests](../art-requests/SKILL.md).

## The loop

```
brief + references -> style bible -> preambles -> A/B engines -> style key + landmarks
                                                                        |
     operator signs <- measure <- one room in the engine <- hero model sheet
```

1. **Brief.** The operator's concepts go in `docs/reference/`, never edited.
2. **Style bible.** Fill [templates/style-bible.md](templates/style-bible.md)
   into `docs/art-pipeline.md` §2 to §4: the style in one line, the eras, the
   hero, the NPCs, landmarks, the composition rules, the always-rules.
3. **Preambles.** Copy [templates/preambles/](templates/preambles/) to
   `art-source/style/prompts/` and replace every `[[MARKER]]` from the bible's
   marker table. The `{fields}` stay: requests fill them.
4. **A/B.** Send one room brief to Sol and to the gateway's Flare, same
   prompt. Put them on one contact sheet, pick by look, record the cost per
   image and a decision: the default engine per kind of image.
5. **Style key.** The first room of the area, `operator-approval: required`.
   Copy the accepted raw to `art-source/style/<area>-style-key.png`. Crop
   recurring landmarks into `art-source/style/landmarks/`. If the game has
   eras, make the key's then-edit and check `align` p90 ≤ 3 px.
6. **Hero model sheet.** Four views on one baseline. One change per round,
   shown to the operator. The accepted sheet hands off to
   [painted-hero](../painted-hero/SKILL.md).
7. **One room in the engine.** Build the style key's room with
   [paint-room](../paint-room/SKILL.md): walk area, hotspots, effects, both
   eras, the hero at scale (the template's placeholder hero is fine before the
   painted one exists).
8. **Measure.** Frame time and video memory in the exported desktop app and
   in Chrome, the browser download, cost per accepted image, hours per asset.
   Evidence in `docs/qa/<plan>/README.md`.
9. **Gate.** Show the operator the room, the screenshots and the numbers.
   Their sign-off is a decision log entry. Only then generate more than three
   rooms of any area.

## Quick start

```sh
mkdir -p art-source/style/prompts art-source/style/landmarks docs/reference
cp <skill>/templates/preambles/*.txt art-source/style/prompts/
# replace every [[MARKER]] from the bible's table, then:
grep -n '\[\[' art-source/style/prompts/*.txt && echo "markers left" || echo "preambles ready"
bun tools/images/new-request.ts art-source/work/specs/style-key.json
bun tools/images/run.ts IMG-0001 && bun tools/images/run.ts IMG-0002     # the A/B pair
tools/adv-art sheet --out build/review/ab.jpg \
  art-source/raw/IMG-0001/IMG-0001-v1.png:Sol art-source/raw/IMG-0002/IMG-0002-v1.png:Flare
```

## Checklist

1. Concepts in `docs/reference/`; style bible filled; every marker replaced.
2. A/B decided and logged: default engine for rooms, edits, NPCs, items.
3. Style key accepted and copied; landmark crops made.
4. Then-edit of the key aligns at p90 ≤ 3 px (if the game has eras).
5. Walk band measured with `adv-art grade --walk-polygon`; a screenshot of
   the hero at the darkest spot of the walk area looked at.
6. Hero model sheet accepted, every round shown to the operator.
7. One room plays in both builds; fps, video memory, download and cost in
   `docs/qa/<plan>/README.md`.
8. Operator sign-off recorded as a decision.

## STOP

- The hero's design drifts between views after three rounds: give the
  operator options (a sketch from them, another engine, a different brief).
- Image spend reaches 80% of the plan's budget: the tool refuses; report.
- A then-edit stays above p90 3 px after two revise rounds.
- The browser build drops below 45 fps with the effects on: profile first.

## Next

[story-track](../story-track/SKILL.md) for the bible and the first part's
puzzle chart, then [paint-room](../paint-room/SKILL.md) for the volume.
