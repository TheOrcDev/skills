# story-track rules

Each rule cost Past a rework or saved it one. Numbers are Past's.

## Story

1. **Never invent story past the signed bible.** A puzzle or scene that needs
   a fact the bible lacks is a STOP: ask the operator. Why: art, voice and
   puzzles are built on the story; a fact made up mid-production gets built
   into fifty rooms before anyone notices.
2. **The operator picks the core from three drafts.** Past's "Thief of names"
   core was picked from three (decision #43); the rest of the bible was
   Claude's proposal, signed by the operator (#48). Mark names and details
   the operator can change as **proposal**.
3. **The bible holds the whole truth in one paragraph**, including every
   twist. Writers need the answer; only the player learns it in pieces.
4. **World rules are numbered and each one earns a puzzle.** A rule that no
   puzzle or scene uses is decoration.
5. **Every part has a turn**: one thing the player learns that changes the
   story, placed where a puzzle pays it off, and written in the bible.
6. **The atlas is the room list.** A puzzle chart may move hotspots and items
   between rooms, but adds no room without a note in the atlas.

## Puzzles

7. **The chart comes before the art.** Each part's Mermaid dependency chart is
   drawn before any of its images are requested (Past `game-design.md` §10).
   Why: the chart decides which rooms need which hotspots, items and then
   images.
8. **No deaths and no dead ends.** No action loses the game, and no item can
   be used up before its last use.
9. **Every puzzle is solvable from information in the game.** For memory
   puzzles, the past shows and the present tests.
10. **Run two or more threads in parallel per area**, so one stuck puzzle
    never stops all progress. Past's prologue ran two threads that met at one
    dark stair; its chapter 1 ran three that met at a clock.
11. **Hints come from the hero, never from a walkthrough screen.** Clicking
    the hero gives a line about the first unfinished goal, more direct each
    time it is asked about the same goal (Past decision #37).
12. **A clue the player can read on screen counts as read.** Writing large
    enough to read in a close-up sets its flag when the close-up opens
    (`Closeup._on_shown`), not only when that line is clicked. Past decision
    #54: a player read "key 13" on a page and could not take the key, because
    only a click on the note counted.
13. **Things to take answer a plain click.** Give them `default_verb = use`.
    Past decision #54: a plain click on a key wall only looked at it, and
    nothing had taught the hold for the verb coin yet.
14. **Teach the hold-for-verb before a puzzle needs it.** Until the player
    first picks a verb on the coin, hotspots that offer more than their click
    show "Hold for more" (Past decision #55). Do not put the first
    coin-only action before that hint can appear.
15. **Every hotspot answers Look.** The rooms test fails otherwise; in Past it
    caught a statue with no Look line.

## Lines

16. **Every spoken line and every response has a static `[ID:…]`.** The ID
    names the voice file and is the translation key (Past decision #21). The
    text behind an ID can change; the ID stays.
17. **IDs are unique across the game, and cues are unique within a file.**
    The lint fails on either. Why: Past's chapter 4 hint goals reused prologue
    cue names and broke the hints file.
18. **Prefix IDs by part and speaker**: `P1_KEEPER_MEET_1`, `HINT_TIDE_2`,
    `JOURNAL_P1_LAST_NIGHT`. Hint goal names are unique game-wide too.
19. **Direction goes in `[#vo=…]` tags, never in the spoken text.** Emotion
    written as narration gets spoken aloud by text-to-speech. Turning-point
    lines always carry direction; every NPC's base direction is in `cast.md`.
    Past's 39 turning-point lines carried `[#vo=…]`.
20. **Write for the voice.** Short sentences, the hero's dry voice, no stage
    directions in the text. Invented names go in the voice tool's
    pronunciation list.
21. **Every new `.dialogue` file goes into
    `internationalization/locale/translations_pot_files`** in `project.godot`.
    The lint fails on a missing or an extra entry.
22. **Comment lines are still read for IDs** by the lint. Never leave a
    commented-out line with a real ID in a game file.

## Proof

23. **Each part has a Playthrough** that plays its whole chain through the
    paths a player's mouse takes: clicks, the verb coin, inventory slots,
    dialogue choices, exits. One GUT test and one QA scenario run the same
    script. Past played the prologue to the epilogue this way in 475 s.
24. **Each part can start mid-game.** Its `chapters.json` entry lists the
    flags, items and memories the earlier parts leave, so its tests and tours
    do not replay the game.
25. **Measure the voice as you write.** The voice tool's `extract` counts
    lines and minutes; Past's script came to 1,069 lines, about 69 minutes,
    which sized the voice budget.
