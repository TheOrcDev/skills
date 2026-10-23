# story-track workflow

Run everything from the repository root. `<skill>` is this skill's folder.

## 1. The interview and the core

1. Ask the operator, one question at a time, only what they can answer:
   - the genre and the tone (with a game or film it should feel like);
   - who the hero is, in one line, and what they want;
   - how long the game is: parts, rooms per part, hours;
   - anything that must happen, and anything that must not.
2. Draft **three cores** in chat. Each is one paragraph: the hero's secret,
   the world's state and why, the ending, and one twist. Make them different
   in kind, not variations of one idea.
3. The operator picks. Add a row to `docs/decisions.md` with their words.

## 2. Bible, cast and atlas

```sh
mkdir -p docs/story
cp <skill>/templates/bible.md <skill>/templates/cast.md <skill>/templates/atlas.md docs/story/
```

1. **`bible.md`:** the truth in one paragraph, the numbered world rules, the
   parts with their turns, the ending. Mark what the operator hasn't said and
   Claude proposed as **proposal**.
2. **`cast.md`:** one row per character: who they are, what the hero took or
   owes, what they want, how they read by outline (for the painting), their
   base voice direction (for `voice-cast`).
3. **`atlas.md`:** one entry per room: Now (what the present image shows),
   Then (what the past shows, or "—"), Play (people, hotspots, memories,
   puzzle role, exits). The totals table counts rooms, past images, close-ups
   and NPCs per part: that is the art budget's input.
4. Show the operator. Their sign-off is a decision row. From here the bible is
   the only source of story.

## 3. Per part: the puzzle chart

```sh
cp <skill>/templates/puzzles.md docs/story/<part>-puzzles.md
```

1. Draw the Mermaid chart from the atlas and the bible. Every node is a mouse
   action; every edge is "needs". Two or more threads, meeting late.
2. Fill the tables: rooms and exits, items (where found, where used, whether
   kept), memories (kind, room, what it shows), the turn, and the flags in the
   order the chain sets them.
3. Walk the chart backwards from the end. For each step, write where the
   player learns what to do. A step without a reachable clue gets one, or the
   chart changes.
4. Show it on the board (`docs/agent-board.md`) before any request for the
   part's art.

## 4. The script

```sh
mkdir -p content/dialogue/<part>
cp <skill>/templates/sample.dialogue content/dialogue/<part>/<area>.dialogue
```

1. One file per area, plus `items.dialogue` for the part's item lines.
2. Every line: `Speaker: Text. [#vo=direction] [ID:<PART>_<THING>_<VERB>_<N>]`.
   Response lines (`- …`) are spoken by the hero and need IDs too.
3. Cues are `<hotspot>_<verb>`, matching the room script's methods
   (`look_<hotspot>()` calls `Say.line(&"<area>", &"<hotspot>_look")`).
4. Conversations set story flags with `do GameState.set_flag("<flag>")` and
   gate choices with `[if GameState.get_flag("<flag>") /]`.
5. Add each new file to `internationalization/locale/translations_pot_files`
   in `project.godot`, so Godot extracts it for translation. The lint fails
   on a file that isn't listed.
6. Delete the template's commented hint and journal blocks after copying: the
   lint reads `[ID:…]` tags in comments too.

## 5. Hints and journal

1. **Goals:** append the part's goals to `content/hints/goals.gd`, in the
   order the chain finishes them:

   ```gdscript
   {"goal": &"lens", "flag": &"got_lens"},
   {"goal": &"cave", "memory": &"p1_last_night"},
   ```

2. **Hint lines:** for each goal, cues `<goal>_1`, `<goal>_2` and `<goal>_3`
   in `content/dialogue/hints.dialogue`, from a nudge to a near-answer. A goal
   id is unique across the game: the lint fails on a repeated cue.
3. **Journal:** in `content/journal/entries.gd`, add to `MEMORIES` (a title
   and a cue in `journal.dialogue` per memory), `FACTS` (what the hero learns
   about themselves, set with `GameState.learn(&"<fact>")`) and `REWATCH` (a
   title and the room whose `rewatch_<id>()` replays it). If the hero's name
   changes in the story, `hero_name()` returns it from a flag.

## 6. The part and its playthrough

1. **`content/chapters.json`:** add the part with `id`, `title`, `start`
   (its first room), `web`, `rooms`, `closeups`, `characters`, `dialogue`,
   `cutscenes`, and the `flags`, `memories` and `items` a player holds on
   reaching its start. Rooms are listed as they are built.
2. **The playthrough:** `content/story/<part>_playthrough.gd`, a
   `Playthrough` subclass whose `run()` plays the chart along the player's
   mouse paths:

   ```gdscript
   class_name HarbourPlaythrough
   extends Playthrough


   func run() -> void:
   	_start_listening()
   	Chapters.start_state(Chapters.part(&"harbour"))
   	await Rooms.goto(&"harbour_steps", &"default", &"none")
   	await _settle()
   	_talk("Keeper")
   	await _choose("Why is the lamp dark?")
   	await _choose("Goodbye.")
   	await _settle()
   	check.call(GameState.get_flag(&"keeper_met"), "the keeper explains the lamp")
   	await _verb("Board", &"look")
   	await _leave("ToShed", &"net_shed")
   	await _click("Rope")
   	check.call(Inventory.has(&"rope"), "taking the rope")
   	await _shot("01_the_rope")
   	_stop_listening()
   ```

   The helpers: `_click`, `_verb(name, verb)`, `_talk`, `_choose(text)`,
   `_leave(exit, room)`, `_give(item, hotspot)`, `_click_slot`,
   `_closeup_click`, `_close`, `_until_memory`, `_settle`, `_shot`.
3. **The GUT test:** `test/integration/test_<part>.gd`, shaped like
   `test_greybox_chain.gd`: reset `GameState`, run the playthrough with
   `check` bound to `assert_true`, wait for it to finish, assert the last room.
4. **The QA run:** `--qa=<part>` plays `content/story/<part>_playthrough.gd`
   in the game, with screenshots from `_shot`. No registration needed.

## 7. Check

```sh
tools/test.sh                                              # import, GUT (with the playthrough), lint
tools/build/export.sh macos
"build/macos/<Game>.app/Contents/MacOS/<Game>" -- --qa=<part> --qa-out="$PWD/docs/qa/<plan>/<part>"
```

The lint fails on: a spoken line or response without an `[ID:…]`, an ID used
twice in the game, a cue defined twice in one file, a dialogue file missing
from (or wrongly listed in) `translations_pot_files`, and a room without a walk
area, a `default` marker, or a hotspot id and name. The every-room GUT test
(`test_rooms_all.gd`) fails on a hotspot with no Look answer. Fix the content,
not the checks.

Then hand the atlas entries to [paint-room](../paint-room/SKILL.md) and the
cast to [skinned-npc](../skinned-npc/SKILL.md).
