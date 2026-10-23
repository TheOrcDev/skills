---
name: story-track
description: Writes a point-and-click adventure's story and puzzles so they can be built and tested. Interviews the operator and drafts three story cores, then writes the signed bible, cast and room atlas; per part, draws a Mermaid puzzle dependency chart before any art, then the Dialogue Manager script with static [ID:…] line IDs and [#vo=…] voice direction, hint goals, journal entries, the chapters.json part and a Playthrough script that GUT and a QA scenario both run. Use when the user wants a story, plot, characters, chapters, rooms list, puzzles, a puzzle chart, dialogue, hint lines or journal pages for an adventure game, when a puzzle is unclear or a player gets stuck, or when they say "story bible", "atlas", "puzzle chart", "write the script" or "playthrough".
---

# story-track

Adventure games die of two things: puzzles the player can't solve from what
the game shows, and stories that change while the art is being made. This
skill fixes the story first, in documents the operator signs, then charts each
part's puzzles before a single room is painted, then writes every line so the
lint, the voice tool and the playthrough test can all read it.

Read [RULES.md](RULES.md) first. Commands are in [WORKFLOW.md](WORKFLOW.md).

## The loop

```
interview -> three cores -> operator picks -> bible + cast + atlas -> operator signs
                                                                         |
   per part:  puzzle chart -> script + hints + journal -> playthrough (GUT + QA) -> art
```

1. **Interview.** Ask what only the operator can answer: genre and tone, the
   hero's idea, how long, what must happen. Offer **three drafted cores**, each
   a paragraph with its twist. The operator picks one; record a decision.
2. **Bible, cast, atlas** from [templates/](templates/), in `docs/story/`. The
   operator signs them; record a decision. From here, the bible is the only
   source of story.
3. **Per part, before its art:** the puzzle chart
   ([templates/puzzles.md](templates/puzzles.md)) in
   `docs/story/<part>-puzzles.md`: the Mermaid chart, rooms and exits, items,
   memories, the turn, the flags in order.
4. **The script:** `content/dialogue/<part>/*.dialogue`
   ([templates/sample.dialogue](templates/sample.dialogue)). Every hotspot's
   Look line, every NPC's tree, the item lines, the memories' voice-over.
5. **Hints and journal:** goals in `content/hints/goals.gd` with cues in
   `hints.dialogue`; memory pages, facts and rewatches in
   `content/journal/entries.gd` with cues in `journal.dialogue`.
6. **The part** in `content/chapters.json`, and its **Playthrough** in
   `content/story/<part>_playthrough.gd`, run by a GUT test and a QA scenario.
7. **Lint and test**, then hand the atlas entries to
   [paint-room](../paint-room/SKILL.md).

## Quick start

```sh
mkdir -p docs/story content/dialogue/<part> content/story
cp <skill>/templates/{bible,cast,atlas}.md docs/story/
cp <skill>/templates/puzzles.md docs/story/<part>-puzzles.md
# write; add each new .dialogue to internationalization/locale/translations_pot_files in project.godot
tools/godot.sh --headless --script res://addons/adv_tools/lint.gd
tools/test.sh
```

## Per part checklist

1. Chart drawn from the signed bible; nothing in it that the bible lacks.
2. Two or more threads in parallel; no death, no dead end, no item lost.
3. Every step's clue is visible or spoken somewhere the player can reach first.
4. Every line has an `[ID:…]`; turning points have `[#vo=…]`; IDs unique game-wide.
5. Every hotspot answers Look; things to take default to Use.
6. Hint goals follow the flags in order, three cues each, nudge to near-answer.
7. Journal pages for every memory; facts for what the hero learns.
8. Part in `chapters.json` with the flags that start it mid-game.
9. Playthrough plays the whole chain in GUT and as a QA scenario; lint passes.

## STOP

A puzzle, line or scene needs a story fact that isn't in the signed bible.
Ask the operator; never invent story.

## Next

[paint-room](../paint-room/SKILL.md) builds the atlas's rooms, and
[skinned-npc](../skinned-npc/SKILL.md) the cast. Memories and reveals:
[memory-reveals](../memory-reveals/SKILL.md). Voice:
[voice-cast](../voice-cast/SKILL.md).
