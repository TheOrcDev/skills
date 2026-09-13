---
name: creature-animation
description: Author, gate, preview and install production animation sets for Final Stand creatures (quadrupeds, arthropods, flyers, hybrids) using the Plan 009 pipeline in tools/3d/animation_quality/creatures. Use when adding a creature to the roster, re-authoring a creature's Idle/Locomotion/BasicAttack/Hit/Death/Cast clips, fixing a rejected animation, running the reimport gates or Unity install, or when the user mentions creature animation, bites, deaths, gaits, reels, Plan 009 or the animal roster.
---

# Creature animation (Plan 009 workflow)

One rule set, one pipeline, every creature: existing rig → correction →
species-specific actions → baked exports → independent reimport gates →
labeled reels → Unity install → commit per slice. Read [RULES.md](RULES.md)
before authoring; run [WORKFLOW.md](WORKFLOW.md) commands as written.

## Quick start

```sh
# from the git checkout (not the slim workspace; see WORKFLOW.md)
python3 tools/3d/animation_quality/creatures/pipeline.py --subject wolf --version 2 --trial /tmp/trial --render keys   # iterate
python3 tools/3d/animation_quality/creatures/pipeline.py --subject wolf --version 2 --render all                      # official
python3 tools/3d/animation_quality/creatures/unity_install.py --subject wolf --version 2                              # native install
python3 tools/3d/animation_quality/creatures/subject_report.py --subject wolf --version 2 --notes "..."               # evidence README
python3 -m unittest discover -s tools/tests -p "test_creature_animation_*.py"
```

## New creature checklist

1. Contract comes from `ArtSource/3D/Roster/subjects.json` only (clips, lineage, scale). Never redefine it in tooling.
2. Inspect the production FBX (`inspect_sources.py`); confirm the scaffold rig, bone names, rigid parts, facing.
3. Add a calibration entry in `calibration.py`: family template + species overrides (gait, attack type, death type, jaw). `referenced_bones` must equal the rig's bone set; the tooling test enforces it.
4. Trial with `--trial --render keys`, look at the contact sheet, fix until `gates.evaluate` passes AND it reads right.
5. Official run, Unity install, README, commit with explicit paths, push, board entry.

## The rules that came from operator review (non-negotiable)

- A bite is a bite: real jaw bone (author one if the rig lacks it), jaw opens, head yaws and twists at contact, then closes. No "pecking".
- Four-legged deaths fall to the ground: legs give way, body sinks, ends flat on the side and holds. No bug-like flips onto the back.
- Flyers die by losing flight: descend once to the real ground (anchor offset applied once), wings on the ground and still.
- Arthropods curl; belly-resting bodies keel over (recorded gate decision).
- Locomotion travels: planted soles drift ≤2% body height while the actor moves at nominal speed; loops are pose- and velocity-continuous.
- Use the existing models, textures and rigs. Regeneration and Meshy are fallbacks that need a recorded obstruction; Meshy's quadruped library offers only Walking.

## Do not

- Stage broad paths, touch another agent's files, or commit Unity's meta/settings noise (see WORKFLOW.md).
- Raise a gate threshold to pass; change `gates.py` only with a board entry for the operator.
- Claim art acceptance from a technical pass. Every subject stays "operator visual review pending" until the operator says otherwise.
