# Implementation plans

Execute the plans in the order below unless the dependencies say otherwise. Read
a plan fully before starting, honor its STOP conditions, and update its row here
when it is done. Milestones are described in `../docs/roadmap.md`.

Status values: TODO | IN PROGRESS | DONE | BLOCKED (one-line reason) |
REJECTED (one-line rationale).

| Plan | Title | Milestone | Effort | Depends on | Status |
|---|---|---|---|---|---|
| [001](001-foundations.md) | Foundations: the kit's template as this game, pinned engine and add-ons, both builds, tests | M0 | S | none | TODO |
| 002 | First light: the style bible, the first style key, one room and the hero in the engine (`look-gate`) | M1 | L | 001; an image budget if the gateway is used | TODO: written when 001 is done |
| 003 | Voice of the world: the voice pipeline end to end (`voice-cast`) | M2 | M | 001; the ElevenLabs plan and key | TODO: written when 001 is done |

## Dependency notes

- 002 and 003 are independent after 001 and can run in parallel.
- The story track has no plan file. It runs as interview sessions with the
  operator and starts when 002's look gate passes. Its outputs (bible, cast,
  atlas, puzzle charts and scripts) go in `docs/story/`.
- Later plans are written one milestone ahead, because they depend on what 002
  and 003 measure.
