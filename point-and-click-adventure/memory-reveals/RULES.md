# memory-reveals rules

Each rule cost Past a rework or kept one from happening. The numbers are
Past's.

## The second state

1. **The past is an edit of the present, never a new picture.** Same
   composition, camera, perspective and key-light direction; only the state
   changes. Why: the switch happens in place, so the two must line up pixel
   for pixel. Past's concept pair measured a 0.7 px median before any
   correction.
2. **Gate the pair with `adv-art align`: p90 ≤ 3 px.** Above it, revise the
   edit; after two Sol misses, use the gateway's Sunburst. Every then image
   in Past's 50 rooms passed on its first round (p90 1.02 to 2.35 px).
3. **Both states live in one room scene.** Layers, walk areas and hotspots
   are tagged with an era, and `Room.set_era()` switches them, so the hero
   stays where they stood. A memory whose geography is too different gets a
   separate room and a crossfade, and that is the exception.
4. **The present is graded in the engine.** Deliver it monochrome (or however
   the present looks) and let the shaders control where the past's colour
   returns.
5. **The transition blends two textures.** Render each era's layers and
   composite them with a noise-edged radial front from the anchor. Why:
   stacking screen reads costs more in the browser, screen-texture mipmaps
   are broken in browser builds, and particles inside a `CanvasGroup` vanish
   in WebKit.
6. **Clamp every `pow()` base to ≥ 0 in shaders.** Apple GPUs return NaN for
   a negative base and the screen goes black.

## Memories

7. **A memory gives a clue the chart needs.** The past shows, the present
   tests: what the player sees in the memory is what they use after it.
8. **Every kind records its memory when it ends, watched or skipped.** The
   journal and the hints read `GameState.memories`.
9. **A playable memory shuts the exits and the save menu until its clue is
   found.** A save could not resume inside a memory. Start it from a verb
   without `await`: the verb must return before the player can act.
10. **A clue written large enough to read counts as read once it is on
    screen.** Past's players read a painted clue in a close-up and could not
    use it, because only a click on it counted (Past decision #54).
11. **Every memory can be watched again** from the journal. The room's
    `rewatch_<id>()` returns the cutscene; rewatching restores the room, the
    hero's position and the whole `GameState` afterwards.

## Cutscenes

12. **Every cutscene plays in letterbox and is skippable.** A Skip button
    appears when the mouse moves and fires after a 0.6 s hold; Esc also
    skips. A plain click never skips: players click to move
    lines along (Past decision #37).
13. **Skipping fast-forwards, it doesn't jump.** Every later step finishes at
    once (walks teleport, lines stop, tweens complete) and the script's own
    logic still runs, so a skipped scene leaves the world exactly as a
    watched one does.
14. **Never change the world from animation keys.** A skip jumps a shot to
    its end and passes over its method keys. Flags, items and room changes
    go in the cutscene script.
15. **Reduce camera motion replaces moves with crossfades.** Test every reveal
    and push-in with it on.
16. **A cutscene can end on black.** The fade stays where the script left it,
    so a scene can hand over to a room change without a flash.

## Discovery reveals

17. **Rings are 3:1 and come from the gateway.** Sol can't set a size, so
    ring 0 is a gateway (Flare) image at 3072×1072. Past's four areas'
    twelve rings cost $1.14.
18. **Inner rings are 2× repaints of the ring outside them.** `adv-art reveal
    --sources` cuts a 1536×536 crop around the hero's spot and scales it to
    3072×1072; the gateway's Sunburst repaints it with the detail a closer
    view shows, keeping every shape where it is.
19. **Register each ring at p90 ≤ 3 px.** Past's rings registered at 1.66 to
    2.97 px. Fog in the painting hides the feathered seams.
20. **Leave a lit, empty spot for the hero.** Ring 0's prompt names a
    figure-free landing that stays light, so a small dark figure reads
    there; `feet` in `reveal.json` is that spot.
21. **The zoom is exponential, about one fixed point.** The pull-back never
    seems to pan, and each inner ring fades once the ring outside shows
    enough detail.
22. **A memory vista can reuse a then image.** Past's areas each had one
    colour vista, and each was a room's then image, so no extra ring was
    needed.
