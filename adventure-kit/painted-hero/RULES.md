# painted-hero rules

Each rule cost Past a round, a rework or an operator's "go back". The
evidence names Past's requests (IMG-####) and decisions (#).

## Design

1. **Clothe the hero.** The silhouette of clothes, hair and props is what
   reads at 480 px on a busy background. *Why:* two rounds of a naked shadow
   figure read as grey aliens (IMG-0155, IMG-0156). A coat with a tall
   collar and a shock of hair read as a hero (IMG-0157 v2).
2. **Ask for appeal, and name what to avoid.** The model-sheet prompt says
   what the hero is ("melancholy, gentle, quietly funny") and what it must
   never look like ("never monstrous, never alien"), with the face spelled
   out (round eyes, a real skull and jaw). *Why:* left open, Sol drifts to
   bulbous heads and slanted eyes.
3. **One model sheet before any motion.** Four views on one baseline, the
   same height, transparent, arms clear of the body. Every later sheet uses
   it as a reference. *Why:* every animation sheet matches one drawing, not
   each other's drift.
4. **Change one thing at a time, or one whole coherent redesign, and show the
   operator before committing.** *Why:* a pass that changed body, stance, head
   and smoke together got "very bad, worse than before" and "everything go
   back"; only the one change the operator liked survived. A complete
   redesign from one approved sheet, shown as a reel uncommitted, shipped on
   the first look.
5. **Match the hero to the rooms, not to the rig.** Draw the hero in the same
   medium as the backgrounds (Past: inked comic line, rim light, sparse
   hatching, in the rooms' grey palette). *Why:* the rendered 3D body read as
   "a grey mannequin" next to Sol's painted rooms and NPCs (plan 010's
   brief).

## Pose rig

6. **The rig owns motion; Sol never invents it.** *Why:* drawn free, Sol
   repeated one stride in most frames of a walk (IMG-0159). Over the rig's
   guides, every frame followed its pose.
7. **Keyframe the rig in code.** Motion is data in `pose_rig.py` (keys per
   bone in anatomical swing, tilt and twist), at 24 fps, sampled at any
   output rate. No Mixamo or motion libraries needed (decision #23).
8. **Fix a pose in the rig, never in the paint.** *Why:* the low pick-up's
   deep squat on tiptoe painted as a jump; the rig learned to stoop from the
   waist with flat feet, and the repaint was right on the first round.
9. **Render right, up and down; left mirrors right.** Anchors mirror with the
   sprite. *Why:* a fourth view is a third more painting for nothing; the
   game mirrors `_r` for `_l` and falls back to the nearest direction.
10. **Events and ground speed come from the rig.** Footsteps on each heel
    strike, `grab`, `use`, `give`, `flare` land on the nearest output frame;
    the walk records `ground_px_per_second`. Painting keeps them because each
    painted frame stands where its render stood.

## Guides

11. **8 poses, 4 x 2, on a 1536 x 1024 sheet.** Each cell is 384 x 512. Sol
    returns transparent edits of that sheet at 1536 x 1024; `painted` resizes
    any other size back, so a sheet of another shape is a revise.
12. **Thin and tone-lift the mannequin.** `thin` erodes it (5 px for key
    poses and front and back walks), the lift makes dark front views read
    and caps speculars. *Why:* Sol paints whatever build it sees: an
    unthinned mannequin came back heavy (IMG-0161).
13. **Squeeze front and back views to 80% width** (`"squeeze": 0.8`). *Why:*
    the front and back walks copied the mannequin's broad build and cut the
    coat short (IMG-0163, IMG-0164); squeezed, they came back slim
    (IMG-0174 v2, IMG-0175 v2). The squeeze carries into the frames,
    anchors and leg registration, so the hero stays narrow in the game.
14. **Name the cells by the frame they show** (`walk_r_3`, `use_d_7`,
    `idle_u`), so a key can be reused and the report reads.

## Painting

15. **References in order: guide, model sheet, accepted side walk.** The
    prompt says "edit the first image" and names the second and third. *Why:*
    after the side walk was accepted (IMG-0160 v3), every later sheet matched
    its line and proportions.
16. **Say "copy only the poses, never the mannequin's build"** and say how the
    clothes behave in the motion (coat tails trail, hem sways, hair bobs).
    *Why:* without it the coat came out short and the build heavy.
17. **Ask for clear space between figures and a transparent background, no
    ground, shadow, text or grid lines.** *Why:* touching figures can't be
    cut apart; a ground line or shadow becomes part of the frame.
18. **Three variants, accept one, record why.** Claude picks (Past decision
    #29) and writes the reason in the request's Review table; the operator
    can overrule.

## Frames

19. **Walks: 8 painted frames per direction, played at 8 fps.** The walk
    guide comes from an 8 fps render of the rig's one-second cycle.
20. **Every other action is limited animation: 2 or 3 key drawings plus the
    idle drawing.** Each frame of the rig's animation shows the key whose pose
    (head and both hands) is nearest, so the rig's timing and events hold.
    *Why:* 96 drawings cover 36 animations; painting every frame at the rig's
    12 fps (walks at 8) would be about 860.
21. **A held drawing breathes.** `HeroBody` scales and sways it under 1%
    around the feet (Past: 0.7% over 3.8 s, 0.5% sway over 6.1 s). *Why:* a
    held drawing that never moves reads as a frozen game.
22. **Register on the guide's soles.** `painted` stands each painted figure's
    soles on the guide's, then slides it sideways (within 48 px, fine-tuned
    over 12 px) until the feet overlap best. Only the feet are compared: the
    coat hides the legs and the hair outgrows the mannequin. *Why:* a planted
    foot that moves a few pixels between frames reads as sliding. Past's 93
    cells shifted -36 to +23 px sideways and -32 to +16 px up and down.
23. **Paint out the eyes, draw them in the game.** `painted` finds the round
    bright blobs nearest the rig's eye anchors, records them as the eye
    anchors and fills them with the body's black. *Why:* the game's eyes
    blink, narrow, widen, flare and follow the voice; painted eyes can't.
    A cell with no eyes found (head bowed or turned away) shows none.
24. **Read `painted-report.json` after every build.** Shift and eye count per
    cell. *Why:* a cell that needed a big shift or lost its eyes is the one
    to look at.

## In the game

25. **Grey + alpha, trimmed, imported lossless.** `pack --shaded --style
    painted` packs two bytes a pixel; the import sets `compress/mode=0`.
    *Why:* VRAM compression blocks up painted ink. Colour comes from the
    shader, so the hero can be tinted per era.
26. **Frame-locked stepping.** The actor moves one frame's worth of ground
    (`ground_px_per_second` / fps) each time a walk frame shows
    (`step_with_frames = true`). *Why:* the planted foot never slides, at any
    frame rate (decision #30).
27. **Depth speed 0.6.** Walking up or down the screen covers ground at 0.6x
    the horizontal speed. *Why:* depth reads slower; at 1.0 the hero zooms
    into the distance.
28. **Budget the video memory.** Past's cap for the hero was 128 MiB; the
    painted set measured 26.5 MiB. *Why:* the rendered set was 97 MB of the
    browser pack; painted and trimmed it is 6.1 MB, and the pack fell from
    143.3 to 52.6 MB.
29. **Smoke or tendrils off on a painted body.** Clothes that fray into ink
    carry that look themselves (decision #53 turned Past's tendrils off).
30. **A passing `--qa=hero_anims` is not art acceptance.** The operator sees a
    reel (every action in every direction, a walk across a room) before the
    commit.
