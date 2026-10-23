# skinned-npc rules

Each rule cost Past a rework, or kept one from happening. The numbers are
Past's.

## The painting

1. **One painting per NPC, on real transparency.** `adv-art npc` refuses a
   painting with no alpha channel. Ask for `background: transparent`, and
   check the background is transparent, not painted grey.
2. **It reads by outline.** A hat, a hood, a cloak, a tool, a posture. The
   NPC is small on screen, and the outline is what the player remembers.
3. **Limbs stand clear of the body.** An arm painted against a coat drags
   the coat along when it bends. Pick the variant whose moving parts have
   air around them. Past accepted its first NPC's v2 because its hanging
   arm stood clear of the coat.
4. **Grey, not black, when the hero is dark.** NPCs are mid and light greys
   so the hero's black reads against them and they read against the room.
5. **Nothing has to move that a bone can't move.** There is no lip sync.
   Talking is a bend of the head, body and hands driven by the voice. Past
   hid every NPC's face in shadow; a painted face is fine if its mouth can
   stay still.
6. **Whole, from head to feet**, with a little space around it and no
   ground, shadow or scenery.
7. **The painting counts as facing right.** A room's `npcs` entry with
   `"facing": "left"` mirrors it.
8. **The present is monochrome.** `adv-art npc` greys the painting unless
   `npc.json` says `"keep_color": true`. Keep colour only where the story
   uses it. Past kept one NPC's trace of blue, and nothing else.

## The rig

9. **The `Base` bone runs from the feet up and never moves.** It has no
   parent, and no motion names it, so the feet stay planted whatever the
   rest does. The one exception is an NPC who doesn't stand on the ground:
   one of Past's NPCs rocks its `Base` because it stands in a boat.
10. **4 to 8 bones.** Past's 13 NPCs had 4 to 7, about five on average.
    More bones than parts that move make the weights mushy.
11. **Each bone runs down the middle of the part it moves.** Every mesh
    vertex follows the bones nearest it, by inverse distance to each bone's
    segment. A bone off to one side pulls the wrong pixels.
12. **A held prop gets its own bone,** parented to whatever holds it or to
    `Base` if it stands on the ground. Past's spade had one.
13. **Points are in the painting's own pixels.** `npc.json` uses the raw's
    coordinates; `adv-art npc` moves them into the trimmed texture. Trace on
    `adv-art grid --native`, which keeps the painting's size.
14. **Fix the rig in `npc.json`, never in the scene.** Rebuild with
    `adv-art npc` and `new_npc.gd`. The scene is written fresh each time.

## Motions

15. **Every NPC has `idle`, `talk_a` and `talk_b`.** The actor takes turns
    between the two talk motions, one per line, so a long conversation
    doesn't repeat one gesture.
16. **Loops sway gently.** Past's idles were 0.3 to 4 degrees at 0.1 to
    0.5 Hz per bone, with phases offset so the parts don't move as one.
17. **Talk bends with the voice.** A talk motion's `voice` map gives each
    bone's bend in degrees at full loudness. Without audio, a lively stand-in
    drives it, so silent lines still look spoken.
18. **One-shots are keyed and short.** `loop: false`, a `length` in seconds,
    and per-bone keys of `[seconds, degrees]`, eased between keys. Start and
    end every key list at 0 degrees, so the gesture returns to rest.
19. **A gesture that changes the world is scripted, not keyed.** The room
    script plays `await actor.play(&"lean")`, then changes flags. Nothing in
    a motion sets state.

## In the game

20. **The speaker name is the link.** A dialogue line's speaker must equal
    the NPC's `speaker` or one of its `aliases`, or its subtitle has no
    anchor and its body won't act it. Use an alias when a character's name
    changes in the story; Past had six NPCs speak under two names each.
21. **A hotspot covers the NPC** in the room's `room.json`, with
    `default_verb: talk` and a `pick_priority` above the scenery behind it.
22. **Build the NPC before the room that places it.** `new_room.gd` loads the
    NPC's scene and fails if it is missing.
23. **List it in its part's `characters`** in `content/chapters.json`, so the
    browser build leaves it out when the part doesn't ship there.
