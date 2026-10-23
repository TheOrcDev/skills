# {{GAME_NAME}}: Roadmap

Every milestone ends in something the operator can play or watch in the desktop
build and in the browser build. The order puts the biggest risks first:

1. Can the image pipeline make this look, with an animated hero, at a cost we
   can sustain?
2. Does the adventure core carry this game's interface and cinematics, on
   desktop and in the browser?
3. Do the voices hold up across a long game?

Plans are written one milestone ahead, because each depends on what the one
before measured.

## M0: Foundations · [plan 001](../plans/001-foundations.md)

- The kit's template set up as this game: pinned Godot 4.7.2, Dialogue Manager
  4.1.0 and GUT 9.7.1, LFS, the docs filled in.
- The greybox sample chain plays end to end.

**Exit:** `tools/test.sh` passes, and `--qa=greybox` passes in the exported
macOS app and in Chrome.

## M1: First light, the look · plan 002 (`look-gate`)

- The style bible and the prompt preambles.
- The first area's style key, one room at final quality as a living painting
  ({{both eras if the game has two}}), with the hero walking in it at scale.
- {{The transition, if any.}}
- The hero's model sheet and animation route.

**Exit:** 60 fps in both builds, a time and cost log per asset. **Gate:** the
operator signs off the look.

## M2: Voice of the world · plan 003 (`voice-cast`)

- The voice pipeline end to end: casting, generation, check, post.
- The hero's voice and one NPC voice, 20–30 lines with subtitles.
- Ambience loops, one-shot effects and one theme.

**Exit:** it all plays in the M1 room in both builds, and the credit spend is
logged against the ceiling. M2 can run in parallel with M1.

## S: Story track (parallel, starts once M1's look is approved) · `story-track`

- A story bible that answers `game-design.md` §13.
- The cast and the atlas (every room's now, then and play).
- Per part: the puzzle dependency chart, then the script with voice direction.

Run as interview sessions with the operator. Claude drafts and the operator
decides.

**Exit:** the first part can be produced without inventing story on the fly.

## M3: Vertical slice · plan {{N}}

- The first part at final quality: rooms, NPCs, close-ups, items, at least one
  of each special moment it needs, a discovery reveal, full voice, music and
  sound.
- 10–20 minutes of play.

**Exit:** published privately as desktop downloads and in the browser, with
real production metrics (hours and credits per room, NPC, reveal and minute of
voice). The operator then sets the number of parts.

## M4+: Parts

One milestone per part:

1. puzzle chart and script;
2. the area's style key;
3. rooms in batches of three or four;
4. NPCs;
5. close-ups, items, memories and the reveal;
6. the part's playthrough in GUT and as a QA scenario in both builds;
7. voice;
8. playtest.

Each part ships playable.

## Release

- Performance and size budgets (`technical-plan.md` §10).
- Store pages with AI-content disclosure, from the receipts and manifests.
- macOS signing and notarization, Windows and Linux builds.
- Launch.
