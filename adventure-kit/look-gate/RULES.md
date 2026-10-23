# look-gate rules

Each rule cost Past a rework or saved it one. Numbers are Past's.

## Order

1. **Prove the look before the volume.** One room, built in the engine with
   the hero in it, signed by the operator, before more than three rooms of
   any area exist. Why: a style that fails in the engine fails 50 times.
   Past's first light cost $0.46 of image spend and about a day.
2. **Prove it in the browser build too**, if the game ships there. Past
   measured 120 fps in the macOS app and 60 fps in Chrome at 1080p, with
   87.6 to 101.7 MiB of video memory, before committing to the look.
3. **Every area's first room is its style key.** Later rooms of the area
   reference the key, not each other. Why: references of references drift.
4. **The operator sees every style key and every hero design round.** Routine
   picks after that are Claude's, recorded with a reason (Past decision #29).

## Prompts

5. **Write the preambles once, from the bible.** Every request of a kind
   starts from its preamble, so 165 requests kept one style in Past. Fix a
   problem in the preamble, not in one request.
6. **Replace every `[[MARKER]]` before the first request.** The request tool
   only checks `{fields}`; a leftover marker goes to the model as text.
7. **"Paint a NEW scene (do not copy the reference's layout)".** A style
   reference pulls its composition along with its style unless told not to.
8. **No people, figures, animals or creatures in backgrounds.** The hero and
   NPCs are separate layers; a painted figure would stand frozen in the room.
9. **No text, letters or numbers, no watermark, signature or border.**
   Generated lettering is gibberish and cannot be translated. A close-up that
   needs readable writing asks for it in its `{lettering}` field.
10. **A then image is an edit of the accepted now image, never a new
    generation.** Past measured its concept pair at scale 1.0012 and under a
    pixel of offset, and 42 then-edits all aligned on the first round. The
    gate is `adv-art align` p90 ≤ 3 px.
11. **The key light keeps its direction in both eras**, so shapes still match
    while one era dissolves into the other.
12. **If eras differ by colour, deliver the colourless era greyscale** and
    tint it in the engine. Why: the shaders then control exactly where colour
    returns, and NPC paintings and icons can be graded to match.

## Composition

13. **The walk band sits against values the hero reads on.** A dark hero
    needs mid-to-light values behind the path; the darkest values go in the
    foreground framing and the top corners. Measure with
    `adv-art grade --walk-polygon` and look at a screenshot of the hero at the
    darkest spot.
14. **Horizon at 40 to 55% of the frame; floor in the lower 30 to 40%; exits
    at the edges or as visible doors.** Why: the hero needs room to walk and
    the player needs to see where the room leads.
15. **Three to six interactive objects, each separated by rim light, haze or
    value**, so hotspots can be found with labels off.
16. **Foreground occluders never hide a hotspot.**
17. **Draw at the largest on-screen size and only scale down.** Upscale only
    where the camera pushes in past the generated size.

## Engines

18. **A/B on the same brief, decide by look, record the cost.** Past's A/B
    made Flare the default for new gateway images and Sunburst for edits
    (decision #28, about $0.028 for a medium 2560×1440 image). Its later Sol
    spike moved most images to Sol at $0 (decision #47).
19. **Sol for most images, the gateway for masks and exact sizes.** Sol's
    landscape images are 1672×941; rooms upscale 1.15× with Lanczos. Vista
    rings at 3:1 need the gateway.

## The hero

20. **Clothes give the silhouette.** Past's naked hero figures read as grey
    aliens (IMG-0155, IMG-0156), and a bald variant read as a horror figure
    rather than a hero (IMG-0158). A coat, a collar and hair made a hero
    (IMG-0157 v2).
21. **One change at a time, or one whole coherent redesign, and show the
    operator before committing.** Past once bundled a leaner body, a new
    stance, a new head and new smoke into one pass; the operator asked for all
    of it back and kept only the smoke.
22. **Four views on one shared baseline, the same height, hands clear of the
    body in front and back views.** The animation paintings need to see the
    hands, and the baseline keeps the views comparable.
23. **The hero reads everywhere on the walkable area**, including the darkest
    room. A thin rim line or rim light keeps a dark hero off dark stone.
24. **The model sheet is a reference, not a sprite.** Animation comes from
    paintings over a rig's poses ([painted-hero](../painted-hero/SKILL.md));
    Sol drawing a walk freehand repeated one stride in most frames.

## Measuring

25. **Measure the same things every time:** frame time at 1080p in the
    exported desktop app and in a visible Chrome window, video memory, the
    browser download, cost per accepted image and hours per asset type. Past's
    numbers became every later estimate.
26. **Grain covers banding.** The Compatibility renderer shows 8-bit steps in
    smooth gradients; Past measured 22.6% of the smoothest pixels on flat
    plateaus without grain and 5.3% with it.
27. **Warm up shaders under black.** The first flashback in Past stalled
    32 ms on macOS and 141 ms in Chrome while its shaders compiled; drawing
    the other era once while a room fades in removed it.
