---
name: painted-hero
description: Designs and animates a point-and-click game's main character as hand-painted 2D frames. A Blender mannequin rig supplies every pose, Sol (GPT-6.1 through Codex) paints the character over 4x2 pose-guide sheets, and adv-art cuts each painted cell back into the render frame, stands it on the guide's soles, paints out the eyes and packs grey + alpha sprite sheets with the rig's anchors, events and ground speed. Walks get 8 painted frames per direction; other actions get 2 or 3 key drawings held on the rig's timing. Use when the user wants to design or animate the hero or main character, make a walk cycle, sprite sheets or idle, talk, pick-up, use or give animations, add a new action, fix sliding feet or legs that change between frames, or says the hero looks off next to the painted backgrounds; or mentions painted frames, pose guides, model sheet, limited animation, build_hero.sh or /painted-hero.
---

# painted-hero

An image model cannot animate. Asked for a walk cycle, Sol repeated one stride
in most frames (Past, IMG-0159). Given a pose to paint over, it paints every
frame right. So the rig owns the motion and Sol owns the look: the rig renders
a grey mannequin in every pose, Sol repaints the mannequin as the hero, and
the tools put each painted drawing back exactly where the mannequin stood,
with the rig's anchors, footsteps and ground speed still true.

Read [RULES.md](RULES.md) before the first request. Run
[WORKFLOW.md](WORKFLOW.md) commands as written. The spec format is in
[references/painted-json.md](references/painted-json.md); the request prompts
are in [references/requests.md](references/requests.md).

## The loop

```
model sheet -> pose rig -> guides -> Sol paints -> cut + register -> pack -> in the game
     ^                       ^                           |                     |
     |                       +---- revise the sheet <----+   painted-report    |
     +------------------- operator sees the reel, one change at a time <-------+
```

1. **Model sheet.** One Sol request: four views (profile, front, back,
   three-quarter) on one baseline, transparent. Give the hero clothes: the
   silhouette of a coat, hat or hair is what reads. Accept one variant and
   show the operator before any animation.
2. **Pose rig.** `scripts/pose_rig.py` renders the mannequin in every
   animation (idle, walk, talk_a, talk_b, look_around, fidget_a, fidget_b,
   use, give, pickup_low, pickup_high, flare) and direction (r, u, d; left
   mirrors right), with anchors.json. Fix a pose in the rig, never in paint.
3. **Guides.** `tools/adv-art painted --guides` lays 8 rig frames 4 x 2 on a
   1536 x 1024 sheet: thinned, tone-lifted, and squeezed to 80% width from the
   front and back.
4. **Sol paints** each sheet through [../art-requests](../art-requests/SKILL.md):
   references in order guide, model sheet, accepted side walk. 3 variants,
   accept the one whose every cell follows its guide.
5. **Cut and register.** `tools/adv-art painted` cuts each cell, maps it into
   the render frame, stands it on the guide's soles, finds and paints out the
   painted eyes, and writes frames plus anchors.json.
6. **Pack.** `tools/adv-art pack --shaded --style painted` trims and packs
   grey + alpha sheets and a manifest; the sheets import lossless;
   `import_sprites.gd` writes `content/characters/hero/hero_sprites.tres`.
7. **In the game.** `HeroBody` draws the painted frames, breathes on held
   drawings, and draws the eyes that blink and flare. Check with
   `--qa=hero_anims`, then a reel for the operator.

`tools/build/build_hero.sh` runs steps 2 (only when the rig's renders are
missing), 5 and 6 in one go.

**Day one, before any painting:** the template's hero is a stand-in drawn in
code (`tools/adv-art placeholder-hero --out art-source/work/characters/hero`,
packed with `adv-art pack --shaded`), in the rig's format with every
animation. The game plays with it until the painted set replaces it
([WORKFLOW.md](WORKFLOW.md), "Day one").

## Quick start

```sh
export HERO_BASE_MESH=art-source/vendor/human-base-meshes/body_male_realistic.blend
cp <this skill>/scripts/pose_rig.py tools/blender/pose_rig.py      # the game owns its rig
cp <this skill>/templates/painted.json art-source/work/characters/hero/painted.json
tools/build/build_hero.sh --guides          # renders + 12 guide sheets in .../hero/guides/sheets/
# per sheet: request it (references/requests.md), run, review, accept, set "raw" in painted.json
tools/build/build_hero.sh                   # frames, sheets, manifest, hero_sprites.tres
tools/test.sh && tools/godot.sh -- --qa=hero_anims --qa-out="$PWD/build/qa/hero"
```

## Per-sheet checklist

1. The guide's 8 poses are distinct and read at thumbnail size.
2. Every painted cell follows its guide: same pose, place and size, no two
   figures touching, nothing painted outside the figure.
3. The design matches the model sheet and the accepted side walk: same
   proportions, clothes, hair, line weight.
4. `painted-report.json`: each cell's `shift` stays near Past's range (-36 to
   +23 px sideways, -32 to +16 px up and down) and its `eyes` count fits the
   view (r: 1, d: 2, u: 0). Look at every cell outside that.
5. In the game: the walk never slides, the planted foot stays planted, every
   action plays past its middle in `--qa=hero_anims`, eyes blink.
6. The operator has seen the reel before the commit.

## Next

NPCs: [../skinned-npc](../skinned-npc/SKILL.md). Proof in both builds:
[../ship-check](../ship-check/SKILL.md).
