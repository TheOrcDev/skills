# paint-room rules

Each rule cost Past a rework, or kept one from happening. The numbers are
Past's.

## Images

1. **Backgrounds have no people in them.** The hero, NPCs and memory figures
   are separate layers. A painted figure can't walk, talk or leave.
2. **No text, letters, numbers, signatures, frames or watermarks** in a room.
   Readable writing belongs in a close-up, where it is painted large on
   purpose.
3. **The present ships greyscale.** `adv-art room` makes the now image
   monochrome, and the engine tints it, so the flashback shaders control
   exactly where colour comes back. `"now_grade": "keep"` is for a room the
   story keeps in colour, and nothing else.
4. **Compose for play, not for a poster.**
   - The camera is at eye level or a little above, with the horizon at 40 to
     55% of the frame.
   - Open floor fills the lower 30 to 40%, with exits at the edges or as
     visible doors.
   - The walk band sits against mid-to-light fog when the hero is dark. The
     darkest values belong in the foreground framing and the top corners.
   - There are 3 to 6 interactive objects, each separated from its
     background by rim light or fog.
   - Why: in Past, a painting that looked right but put black behind the
     walk band hid the hero.
5. **The area's first room is its style key.** No more than three rooms of
   an area are generated before the key is accepted. Every room of the area
   references the key ([look-gate](../look-gate/SKILL.md)).
6. **The then image is an edit of the accepted now image, never a new
   painting.** The same composition, camera, horizon and light direction.
   Why: a flashback switches eras in place, and the hero has to stand on the
   same floor in both. Past measured its concept pair at a median of 0.7 px
   before any correction.
7. **Gate the pair at p90 ≤ 3 px** with `adv-art align`, and record the
   report. Above it is a revise round. After two Sol misses, use the
   gateway's Sunburst for the edit. Past: every one of 42 then-edits passed
   on its first round, at p90 1.02 to 2.35 px.
8. **Sol's images are 1672 × 941 whatever the request's size says.**
   `adv-art room` upscales them 1.15× with Lanczos to 1920 × 1080. Draw
   nothing that needs more than that unless the camera never pushes past it.
9. **Raws are never edited, renamed or deleted.** `room.json` points at
   `art-source/raw/IMG-####/IMG-####-vN.png` as delivered, and every
   processed image goes to `content/rooms/<id>/art/` or
   `art-source/work/`.

## Data and scenes

10. **The room is data.** Edit `room.json`, rebuild with `adv-art room`, and
    rerun `new_room.gd --replace`. Never hand-edit a room's `.tscn`. Why:
    Past hand-wrote one build script per room for its first two rooms. With
    50 more coming, they became one data file each.
11. **The room script is yours; the scene is the scaffold's.** `new_room.gd`
    writes `<id>.gd` only when it is missing and never overwrites it, so
    rebuilding the scene keeps the code.
12. **Trace on the grid, check on the overlay.** Polygons are in 1920 × 1080
    pixels. Look at the overlay image before building: the walk polygon
    hugging the floor, each hotspot on its object, each `walk_to` dot inside
    the walk area, and the markers on open floor.
13. **Every room has a `default` marker.** It is where the hero lands when
    nothing names an entry, and the every-room test fails without it.
14. **Every exit lands.** Its `room` exists, and its `entry` marker exists in
    that room. Name entry markers `from_<room>` after the room they come
    from, so the two ends of a door are easy to pair.
15. **Every hotspot answers Look.** A hotspot whose default verb is not
    `look` also needs that verb's method. The every-room test checks both.
    Past's test found a statue with no Look line on its first run.
16. **A story gate on an exit is `requires_flag`.** Until the flag is set,
    the exit answers `locked_<exit_id>()` in the room script. Never hide or
    move an exit to lock it.
17. **A thing that leaves the room is a prop on a clean plate.** Request the
    clean plate as an edit of the accepted now image with the thing removed.
    `room.json` names the plate and traces each prop, and the room script
    hides the prop's layer and hotspot from flags in `_on_enter`. Past did
    this for a crate and a stretcher.
18. **A past-only or present-only hotspot carries `era`.** Without it, a
    hotspot answers in both eras.
19. **Overlapping hotspots need `pick_priority`.** Higher wins. A person
    standing in front of a door is the usual case.
20. **Occluders are optional.** `room.json` can trace walk-behind cut-outs,
    cut from both eras with their baseline at the polygon's lowest point.
    Past's 50 rooms needed none; the first room used four.

## Close-ups and items

21. **Writing the player can read counts as read.** A close-up whose writing
    is large enough to read sets its flag in `_on_shown()`, not only when
    the line is clicked. Why: Past's players read a key number on a page and
    then couldn't take the key, because only a click on the note counted
    (decision #54).
22. **Write the close-up's script before `new_closeup.gd`.** The scaffold
    attaches `content/closeups/<id>/<id>.gd` only if it already exists.
23. **List a close-up's small hotspots before its catch-all one, and give
    them a higher `pick_priority`.** A page with a note on it needs the note
    to win.
24. **One item sheet per part.** `adv-art icons` finds the objects in
    reading order and fails if the count doesn't match the names. Ask for
    a grid with generous space between objects so none touch.
25. **Icons go grey with the present** unless they are named in `--colour`.
    Colour is a story signal; spend it on purpose.
26. **Combinations are written both ways** in the items list: `rag + oil`
    and `oil + rag` make the same item.

## Production

27. **Work in batches of three or four rooms.** Sol paints batch N+1 while
    batch N is built. Past built 50 rooms in about 4.5 hours of commit time
    this way.
28. **Budgets per room:** under 400 MiB of video memory with both eras, the
    hero and the NPCs loaded; under 1 s to load; frame p95 under 16.7 ms at
    1080p. Past measured 102 to 144 MiB, 29 to 258 ms and 8.3 to 16.7 ms
    across 52 rooms.
29. **The depth model runs on the machine.** `adv-art room` estimates depth
    for the fog. Install its extra once (`uv sync --extra depth` in
    `tools/art`) before the first build.
