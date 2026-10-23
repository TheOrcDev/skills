# {{GAME_NAME}}: Game Design Document

Status: draft, {{DATE}}. The story stays open until the story track settles it
(see `roadmap.md`). Confirmed operator decisions are listed in
`decisions.md`. Anything marked *proposal* here still needs the operator's
approval.

## 1. Concept

**Genre:** Point-and-click adventure in the LucasArts tradition: verb coin,
inventory, dialogue trees, no deaths, no dead ends.
**Platform:** {{PLATFORMS: for example, desktop downloads (macOS, Windows,
Linux) and the browser}}.
**Controls:** Mouse only.
**Length:** {{LENGTH: set in the story track}}.
**Tone:** {{TONE and the closest reference game}}.
**Look:** {{LOOK: one or two sentences, for example the medium, the palette
and what the past or second state looks like}}. Concepts are in `reference/`.
**Audio:** Fully voiced. Voice, sound effects and music are made with
ElevenLabs.

**Logline (draft):** {{LOGLINE}}

| Concept | What it shows |
|---|---|
| {{reference/concept-01.png}} | {{what it shows and what it is for}} |

## 2. The hero

- **Look:** {{silhouette first: shape, clothes, the one feature people
  remember}}. The hero reads by outline at about 44% of the screen height.
- **Name:** {{NAME, and why the hero is called that}}.
- **Acting:** {{how the hero performs: face, eyes, posture, voice}}. If the
  hero has no visible mouth, the eyes or another feature follow the voice
  envelope instead of lip sync.
- **Personality (proposal):** {{PERSONALITY}}. Most of the game's jokes live in
  the hero's look descriptions and dialogue options.
- **Who the hero really is:** the answer goes in the story bible, not in this
  document.

## 3. Design pillars

1. {{PILLAR: the visual rule of the world, for example "memory is colour"}}
2. **Every arrival is a reveal** (if the game uses discovery reveals): a new
   area opens with a scenic establishing shot that pulls back to the whole
   landscape, then settles into the playable room.
3. {{PILLAR: how the special mechanic serves the puzzles}}
4. **Mouse only, LucasArts rules.** A verb coin, an inventory and dialogue
   trees. No deaths, no dead ends and no pixel hunts: hotspots have hover labels
   and can be revealed.
5. {{PILLAR: tone}}. Everything is voiced and subtitled, and every cutscene can
   be skipped and rewatched.

## 4. Core loop

```
Arrive in a new area → establishing shot → control returns
  → explore: look / use / talk through the verb coin; collect items
  → find {{THE_SPECIAL_THING: a memory anchor, a clue, a mechanism}}
  → {{THE_SPECIAL_MOMENT: a flashback, a vision, a state change}}
  → use what it showed to solve the present-day puzzle
  → the journal records it; a new question opens
  → the way to the next area opens
```

## 5. World structure

- **Game → parts (chapters) → areas → rooms.** Parts are listed in
  `content/chapters.json`.
- **Area:** a region with its own vista, its own music theme and its own style
  key. It has a few rooms.
- **Room:** one playable screen at 1920×1080, sometimes scrolling sideways up
  to three screens. A room can carry a second era layer ("then") that the
  special moments use.
- {{CANDIDATE_AREAS}}

## 6. Flashbacks and two-state rooms

{{Delete this section if the game has no second state.}}

| Type | What happens | When |
|---|---|---|
| **Vision** (default) | The room's other layer fades in and the camera moves. A moment plays out and the hero reacts in voice-over. 30–90 s, skippable, rewatchable from the journal. | Most anchors |
| **Playable memory** | The other version of the room becomes interactive for a short sequence, with its own hotspots and possibly items. Its exits and the save menu are shut until its goal is met. | Key story and puzzle beats only |
| **Memory vista** | A discovery reveal played in the other era. | Area and part milestones |

**Triggers:** always caused by the player, by examining or using something or
by entering a place after a story beat. Never random, and never in the middle
of a dialogue.

**Look and sound:** {{how the transition looks and sounds both ways}}. A
**Reduce flashing** setting softens any flare.

## 7. Discovery reveals

- The first entry into an area plays its reveal. It can be skipped and
  rewatched.
- **Shot grammar:** start close on the hero at the area's threshold. Pull back
  through two or three nested paintings, each covering twice the area of the
  last, until the whole landscape shows. Hold on the area's title card, then
  push back into the first playable room.
- Letterbox bars (2.39:1) mark every non-interactive sequence.
- **Living painting:** drifting fog layers, parallax between depth layers,
  birds, ash or rain, flickering light and water shimmer.

## 8. Controls (mouse only)

| Action | Mouse |
|---|---|
| Walk | Left-click the ground |
| Leave quickly | Double-click an exit |
| Default action | Left-click a hotspot. Doors open, people talk, a thing with only one use is used, everything else is looked at. Writing in a close-up counts as read once it is on screen. |
| Verb coin | Press and hold left on a hotspot (300 ms), then release over Look, Use or Talk. Until the player first picks a verb on it, a hotspot's label adds "Hold for more" wherever the coin offers more than a click. |
| Inventory | Right-click. Right-click again or click outside to close it. |
| Use an item on something | Pick the item in the inventory, then left-click a hotspot or another item |
| Drop the held item | Right-click while holding an item |
| Dialogue | Click a line. A left-click skips the line being spoken. |
| Skip a cutscene | Move the mouse to show Skip, then press and hold it (0.6 s) |
| Start screen | The game opens on it: Continue, New Game, Load Game, Settings, Quit (no Quit in the browser) |
| Menu | Push the cursor against the top edge to reveal a bar: Journal, Save, Load, Settings, Reveal hotspots, Main menu, Quit |
| Hint | Click the hero, who thinks aloud about the current goal |

The keyboard is never required. Esc is an optional extra that skips and closes.

## 9. Interface

- **Verb coin:** a ring with three glyphs: Look, Use (take, open, push) and
  Talk. {{GLYPH_STYLE}}
- **Hover:** the hotspot name appears near the cursor, and the cursor changes
  shape over hotspots and exits.
- **Inventory:** a band that stays open while items are picked and combined.
  Items can be examined, combined, used on hotspots or given to people.
- **Dialogue:** branching options. Exhausted options disappear and important
  questions stay. Subtitles are on by default and coloured per speaker.
- **Journal:** {{what the journal collects}}. Every cutscene, flashback and
  reveal can be rewatched from here.

## 10. Puzzle design rules

- No deaths and no dead ends.
- Every puzzle can be solved from information in the game. For two-state
  puzzles, the other state shows and the present tests.
- Each part gets a **puzzle dependency chart** before any art is produced.
- Run several puzzle threads in parallel per area, so one stuck puzzle never
  stops all progress.
- Hints come from the hero, never from a walkthrough screen.
- A clue the player can read on screen counts as read.

## 11. Audio direction

- **Present:** {{the sound of the present}}.
- **Past or second state:** {{the sound of the other state}}.
- **Voice:** {{the hero's voice}}. Every NPC voice is distinct.
- Production details are in `audio-pipeline.md`.

## 12. Accessibility and settings

Separate volumes for voice, music, effects and ambience. Subtitles on/off and
size. Text speed. Reduce flashing. Reduce camera motion, which shortens or
crossfades the reveal moves and close-up pushes. Fullscreen. Render at 1080p.
Hotspot reveal. Every cutscene is skippable.

## 13. Story track: open questions

These are settled with the operator before the first part's script is written.
The answers go in `story/bible.md`:

1. Who is the hero? This is the answer the whole game builds toward.
2. What happened to the world, and why does the present look as it does?
3. What are the rules of the hero's existence?
4. Who else is in the world, and what do they want?
5. How does the special mechanic work in the world?
6. The part list, the areas in each part, and the ending.
7. The target play time.

## 14. Scope and production approach

- The game is produced part by part, and each part ends playable in the
  desktop build and the browser build.
- **A vertical slice comes first.** It measures what a room, a flashback, a
  reveal, an NPC and a minute of voice really cost, and that turns the length
  into a number of parts the team can make.
